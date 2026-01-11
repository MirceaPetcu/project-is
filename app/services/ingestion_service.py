"""
Data Ingestion Service
Handles ingestion from multiple OSINT sources
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import hashlib
import aiohttp
from bs4 import BeautifulSoup
import feedparser

from ..models.schemas import (
    Source, Document, Entity, IngestRequest,
    SourceType, MisinformationAlert
)
from ..core.config import settings
from .lightrag_service import OSINTLightRAG
from .entity_resolver import EntityResolver
from .credibility_scorer import CredibilityScorer


class DataIngestionService:
    """
    Multi-source data ingestion service
    Supports: RSS/Atom feeds, web scraping, API integration
    """
    
    def __init__(
        self,
        lightrag: OSINTLightRAG,
        entity_resolver: EntityResolver,
        credibility_scorer: CredibilityScorer
    ):
        self.lightrag = lightrag
        self.entity_resolver = entity_resolver
        self.credibility_scorer = credibility_scorer
        self.ingested_docs: Dict[str, Document] = {}
        
    def _generate_doc_id(self, document: Document) -> str:
        """Generate unique document ID"""
        content_hash = hashlib.sha256(
            f"{document.source_id}:{document.title}:{document.published_date}".encode()
        ).hexdigest()[:16]
        return f"doc_{content_hash}"
    
    async def ingest_batch(self, request: IngestRequest) -> Dict[str, Any]:
        """Ingest a batch of documents from a source"""
        source = request.source
        documents = request.documents
        
        # Initialize or get source credibility
        if source.id not in self.credibility_scorer.source_history:
            credibility_score = self.credibility_scorer.initialize_source(source)
            source.credibility_score = credibility_score
        else:
            source.credibility_score = self.credibility_scorer.get_source_score(source.id)
        
        # Register source with LightRAG
        self.lightrag.register_source(source.id, source.credibility_score)
        
        results = {
            "source_id": source.id,
            "documents_processed": 0,
            "entities_extracted": 0,
            "misinformation_alerts": [],
            "errors": []
        }
        
        for doc in documents:
            try:
                # Generate doc ID
                doc.id = self._generate_doc_id(doc)
                
                # Store document
                self.ingested_docs[doc.id] = doc
                
                # Ingest into LightRAG
                await self.lightrag.ingest_document(
                    content=f"Title: {doc.title}\n\nContent: {doc.content}",
                    source_id=source.id,
                    metadata={
                        "doc_id": doc.id,
                        "url": str(doc.url) if doc.url else None,
                        "published_date": doc.published_date.isoformat() if doc.published_date else None,
                        "author": doc.author,
                        "language": doc.language,
                        "location": doc.location
                    }
                )
                
                results["documents_processed"] += 1
                
                # Extract entities if requested
                if request.extract_entities:
                    entities = await self._extract_and_resolve_entities(doc, source)
                    doc.entities_mentioned = [e.id for e in entities]
                    results["entities_extracted"] += len(entities)
                
                # Detect misinformation if requested
                if request.detect_misinformation:
                    alert = await self._detect_misinformation(doc, source)
                    if alert:
                        results["misinformation_alerts"].append(alert)
                
            except Exception as e:
                results["errors"].append({
                    "document": doc.title if hasattr(doc, 'title') else 'unknown',
                    "error": str(e)
                })
        
        return results
    
    async def _extract_and_resolve_entities(
        self,
        document: Document,
        source: Source
    ) -> List[Entity]:
        """Extract and resolve entities from document"""
        # Use LightRAG to extract entities
        raw_entities = await self.lightrag.extract_entities(document.content)
        
        entities = []
        for raw_entity in raw_entities:
            entity = Entity(
                name=raw_entity.get("name", ""),
                entity_type=raw_entity.get("type", "other"),
                sources=[source.id],
                attributes={
                    "context": raw_entity.get("context", ""),
                    "document_id": document.id
                },
                first_mentioned=document.published_date or datetime.utcnow(),
                last_mentioned=document.published_date or datetime.utcnow()
            )
            
            # Resolve entity
            resolution = await self.entity_resolver.resolve_entity(entity)
            resolved_entity = self.entity_resolver.get_entity_by_id(
                resolution.canonical_entity_id
            )
            if resolved_entity:
                entities.append(resolved_entity)
        
        return entities
    
    async def _detect_misinformation(
        self,
        document: Document,
        source: Source
    ) -> Optional[MisinformationAlert]:
        """Detect potential misinformation in document"""
        # Extract main claims from document
        claims = await self._extract_claims(document.content)
        
        for claim in claims:
            # Check against existing knowledge
            contradiction = await self.lightrag.detect_contradictions(claim)
            
            if contradiction["contradiction_score"] >= settings.MISINFORMATION_THRESHOLD:
                # Update source credibility
                self.credibility_scorer.update_score_on_verification(
                    source.id,
                    was_accurate=False,
                    verification_confidence=contradiction["contradiction_score"]
                )
                
                return MisinformationAlert(
                    document_id=document.id,
                    claim=claim,
                    contradiction_score=contradiction["contradiction_score"],
                    contradicting_sources=contradiction.get("evidence", []),
                    evidence=contradiction.get("contradictions", [])
                )
        
        return None
    
    async def _extract_claims(self, content: str) -> List[str]:
        """Extract verifiable claims from content"""
        # Use LLM to extract claims
        prompt = f"""
Extract the main factual claims from the following text.
Focus on verifiable statements about events, people, or facts.

Text: {content[:2000]}

Return a list of claims, one per line.
"""
        
        response = await self.lightrag._llm_model_func(
            prompt,
            system_prompt="You are an expert at identifying factual claims."
        )
        
        # Parse claims from response
        claims = [line.strip() for line in response.split('\n') if line.strip()]
        return claims[:5]  # Limit to top 5 claims
    
    async def ingest_from_rss(
        self,
        source: Source,
        feed_url: str,
        max_items: int = 50
    ) -> Dict[str, Any]:
        """Ingest documents from RSS/Atom feed"""
        try:
            # Parse feed
            feed = feedparser.parse(feed_url)
            
            documents = []
            for entry in feed.entries[:max_items]:
                doc = Document(
                    source_id=source.id,
                    title=entry.get('title', 'Untitled'),
                    content=entry.get('summary', entry.get('description', '')),
                    url=entry.get('link'),
                    author=entry.get('author'),
                    published_date=self._parse_feed_date(entry),
                    language=source.metadata.get('language', 'en')
                )
                documents.append(doc)
            
            # Create ingest request
            request = IngestRequest(
                source=source,
                documents=documents,
                extract_entities=True,
                detect_misinformation=True
            )
            
            return await self.ingest_batch(request)
            
        except Exception as e:
            return {
                "error": str(e),
                "feed_url": feed_url
            }
    
    def _parse_feed_date(self, entry) -> Optional[datetime]:
        """Parse date from feed entry"""
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    return datetime(*time_struct[:6])
        return None
    
    async def ingest_from_web(
        self,
        source: Source,
        url: str,
        extract_method: str = "auto"
    ) -> Dict[str, Any]:
        """Scrape and ingest content from web page"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.text if title else "Untitled"
            
            # Extract main content (simplified)
            # In production, use better extraction like newspaper3k or trafilatura
            content_tags = soup.find_all(['p', 'article'])
            content = '\n'.join([tag.get_text() for tag in content_tags])
            
            doc = Document(
                source_id=source.id,
                title=title_text,
                content=content,
                url=url,
                language=source.metadata.get('language', 'en')
            )
            
            request = IngestRequest(
                source=source,
                documents=[doc],
                extract_entities=True,
                detect_misinformation=True
            )
            
            return await self.ingest_batch(request)
            
        except Exception as e:
            return {
                "error": str(e),
                "url": url
            }
    
    async def ingest_from_api(
        self,
        source: Source,
        api_endpoint: str,
        api_key: Optional[str] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ingest data from API endpoint"""
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint, headers=headers, params=params) as response:
                    data = await response.json()
            
            # Parse API response (format-specific)
            # This is a generic implementation - customize based on API
            documents = self._parse_api_response(data, source)
            
            request = IngestRequest(
                source=source,
                documents=documents,
                extract_entities=True,
                detect_misinformation=True
            )
            
            return await self.ingest_batch(request)
            
        except Exception as e:
            return {
                "error": str(e),
                "api_endpoint": api_endpoint
            }
    
    def _parse_api_response(
        self,
        data: Dict[str, Any],
        source: Source
    ) -> List[Document]:
        """Parse API response into documents (generic)"""
        documents = []
        
        # Handle common API response formats
        items = data.get('items', data.get('results', data.get('data', [])))
        
        if isinstance(items, list):
            for item in items:
                doc = Document(
                    source_id=source.id,
                    title=item.get('title', item.get('name', 'Untitled')),
                    content=item.get('content', item.get('description', item.get('text', ''))),
                    url=item.get('url', item.get('link')),
                    author=item.get('author'),
                    language=item.get('language', 'en')
                )
                documents.append(doc)
        
        return documents
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve ingested document by ID"""
        return self.ingested_docs.get(doc_id)
    
    def get_documents_by_source(self, source_id: str) -> List[Document]:
        """Get all documents from a source"""
        return [
            doc for doc in self.ingested_docs.values()
            if doc.source_id == source_id
        ]
