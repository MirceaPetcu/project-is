"""
LightRAG Integration for OSINT Platform
Adapts LightRAG methodology for multi-source intelligence analysis
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import numpy as np

# Add LightRAG to path
lightrag_path = Path(__file__).parent.parent.parent.parent / "LightRAG"
sys.path.insert(0, str(lightrag_path))

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

from ..core.config import settings
from ..models.schemas import QueryMode, Source


class OSINTLightRAG:
    """
    Extended LightRAG for OSINT platform with:
    - Source credibility weighting
    - Multi-source entity resolution
    - Temporal awareness
    - Geographic clustering
    """
    
    def __init__(self, working_dir: str = None, rag: LightRAG | None = None):
        self.working_dir = working_dir or settings.WORKING_DIR
        self.source_credibility_map: Dict[str, float] = {}
        self.llm_provider = settings.LLM_PROVIDER

        # Determine embedding dimension based on provider
        if self.llm_provider == "ollama":
            embedding_dim = settings.OLLAMA_EMBEDDING_DIM
        else:
            embedding_dim = 1536  # OpenAI default

        # Initialize LightRAG with custom configuration
        self.rag = rag or LightRAG(
            working_dir=self.working_dir,
            kv_storage="RedisKVStorage",
            vector_storage="MilvusVectorDBStorage",
            graph_storage="Neo4JStorage",
            doc_status_storage='JsonDocStatusStorage',
            auto_manage_storages_states=True,
            llm_model_func=self._llm_model_func,
            llm_model_name=settings.OLLAMA_MODEL if self.llm_provider == "ollama" else settings.OPENAI_MODEL,
            llm_model_kwargs=self._get_llm_kwargs() if self.llm_provider == "ollama" else {},
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=8192,
                func=self._embedding_func
            ),
        )
        self.rag_init = False

    async def initialize(self):
        """Asynchronous initialization of LightRAG"""
        if not self.rag_init:
            await self.rag.initialize_storages()
            self.rag_init = True

    async def _ensure_initialized(self):
        """Ensure LightRAG is initialized before any operation"""
        if not self.rag_init:
            await self.initialize()

    def _get_llm_kwargs(self) -> Dict[str, Any]:
        """Get LLM kwargs for Ollama"""
        return {
            "host": settings.OLLAMA_HOST,
            "options": {"num_ctx": settings.OLLAMA_NUM_CTX},
            "timeout": settings.OLLAMA_TIMEOUT,
        }
        
    async def _llm_model_func(
        self,
        prompt,
        system_prompt=None,
        history_messages=[],
        **kwargs
    ) -> str:
        """Custom LLM function with OSINT context - supports Ollama and OpenAI"""
        if self.llm_provider == "ollama":
            # Remove conflicting parameters from kwargs if they exist
            kwargs.pop('host', None)
            kwargs.pop('timeout', None)
            kwargs.pop('options', None)
            return await ollama_model_complete(
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                host=settings.OLLAMA_HOST,
                timeout=settings.OLLAMA_TIMEOUT,
                options={"num_ctx": settings.OLLAMA_NUM_CTX},
                **kwargs
            )
        else:
            return await openai_complete_if_cache(
                settings.OPENAI_MODEL,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=settings.OPENAI_API_KEY,
                **kwargs
            )

    async def _embedding_func(self, texts: List[str]) -> np.ndarray:
        """Custom embedding function - supports Ollama and OpenAI"""
        if self.llm_provider == "ollama":
            # Call ollama_embed directly without .func to use the proper signature
            return await ollama_embed.func(
                texts,
                embed_model=settings.OLLAMA_EMBEDDING_MODEL,
                host=settings.OLLAMA_HOST,
                timeout=settings.OLLAMA_TIMEOUT,
            )
        else:
            return await openai_embed(
                texts,
                model=settings.OPENAI_EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
    
    def register_source(self, source_id: str, credibility_score: float):
        """Register a source with its credibility score"""
        self.source_credibility_map[source_id] = credibility_score
    
    async def ingest_document(
        self,
        content: str,
        source_id: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Ingest a document with source tracking and credibility weighting
        """
        await self._ensure_initialized()
        metadata = metadata or {}
        metadata['source_id'] = source_id
        metadata['credibility_score'] = self.source_credibility_map.get(
            source_id,
            settings.DEFAULT_SOURCE_CREDIBILITY
        )
        metadata['ingested_at'] = datetime.utcnow().isoformat()
        
        # Enhance content with metadata for better retrieval
        enhanced_content = f"""
SOURCE: {source_id}
CREDIBILITY: {metadata['credibility_score']}
CONTENT: {content}
"""
        
        await self.rag.ainsert(enhanced_content)
        return True
    
    async def query(
        self,
        query: str,
        mode: QueryMode = QueryMode.HYBRID,
        only_credible_sources: bool = True,
        min_credibility: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query the knowledge graph with credibility filtering
        """
        await self._ensure_initialized()
        min_credibility = min_credibility or settings.MIN_CREDIBILITY_SCORE
        
        # Map QueryMode to LightRAG query param
        mode_map = {
            QueryMode.NAIVE: "naive",
            QueryMode.LOCAL: "local",
            QueryMode.GLOBAL: "global",
            QueryMode.HYBRID: "hybrid"
        }
        
        param = QueryParam(
            mode=mode_map[mode],
            only_need_context=False,
            **kwargs
        )
        
        # Add credibility filter to query
        if only_credible_sources:
            enhanced_query = f"""
{query}

FILTER: Only use information from sources with credibility score >= {min_credibility}
"""
        else:
            enhanced_query = query
        
        result = await self.rag.aquery(enhanced_query, param=param)
        
        return {
            "answer": result,
            "query": query,
            "mode": mode.value,
            "credibility_filter": min_credibility if only_credible_sources else None
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using LLM
        """
        prompt = f"""
Extract all named entities from the following text. For each entity, provide:
- name: The entity name
- type: person, organization, location, event, or other
- context: Brief context about the entity in the text

Text: {text}

Return the entities in a structured format.
"""
        
        response = await self._llm_model_func(
            prompt,
            system_prompt="You are an expert at entity extraction for intelligence analysis."
        )
        
        # Parse response (simplified - in production, use structured output)
        return self._parse_entity_response(response)
    
    def _parse_entity_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM entity extraction response"""
        import json
        import re

        entities = []

        # Try to parse as JSON first
        try:
            # Look for JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and 'name' in item:
                            entities.append({
                                'name': item.get('name', ''),
                                'type': item.get('type', 'other'),
                                'context': item.get('context', '')
                            })
                    return entities
        except json.JSONDecodeError:
            pass

        # Fallback: parse line-by-line format
        lines = response.strip().split('\n')
        current_entity = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_entity.get('name'):
                    entities.append(current_entity)
                    current_entity = {}
                continue

            # Match patterns like "name: John Doe" or "- name: John Doe"
            for field in ['name', 'type', 'context']:
                pattern = rf'[-•*]?\s*{field}\s*[:=]\s*(.+)'
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    current_entity[field] = match.group(1).strip()
                    break

        # Add last entity if exists
        if current_entity.get('name'):
            entities.append(current_entity)

        # Ensure all entities have required fields
        for entity in entities:
            entity.setdefault('type', 'other')
            entity.setdefault('context', '')

        return entities
    
    async def detect_contradictions(
        self,
        claim: str,
        existing_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Detect contradictions between a claim and existing knowledge
        """
        if existing_knowledge:
            # Query existing knowledge
            context_result = await self.query(
                f"What do we know about: {claim}",
                mode=QueryMode.HYBRID,
                only_credible_sources=True
            )
            context = context_result['answer']
        else:
            context = ""
        
        prompt = f"""
Analyze if the following claim contradicts known information.

Claim: {claim}

Known Information: {context}

Provide:
1. Contradiction score (0.0 to 1.0, where 1.0 is complete contradiction)
2. Specific contradictions found
3. Supporting evidence for contradictions

If there's no contradiction, score should be 0.0.
"""
        
        response = await self._llm_model_func(
            prompt,
            system_prompt="You are an expert at fact-checking and contradiction detection."
        )
        
        return self._parse_contradiction_response(response, claim)
    
    def _parse_contradiction_response(
        self,
        response: str,
        claim: str
    ) -> Dict[str, Any]:
        """Parse contradiction detection response"""
        # Simplified - enhance with structured output
        return {
            "claim": claim,
            "contradiction_score": 0.0,  # Parse from response
            "contradictions": [],
            "evidence": []
        }
    
    async def find_narrative_patterns(
        self,
        entities: List[str],
        time_window_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Detect coordinated narratives involving specific entities
        """
        entities_str = ", ".join(entities)
        
        prompt = f"""
Analyze patterns in how the following entities are discussed:
Entities: {entities_str}
Time window: Last {time_window_days} days

Identify:
1. Common narratives or themes
2. Coordinated messaging patterns
3. Unusual spikes in mentions
4. Source coordination

Provide detailed analysis of any detected patterns.
"""
        
        response = await self._llm_model_func(
            prompt,
            system_prompt="You are an expert at detecting information campaigns and coordinated narratives."
        )
        
        return self._parse_narrative_response(response)
    
    def _parse_narrative_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse narrative detection response"""
        # Simplified - enhance with structured output
        return []
    
    async def predict_emerging_patterns(
        self,
        context: str = None
    ) -> List[Dict[str, Any]]:
        """
        Predict emerging patterns before they become mainstream
        """
        if not context:
            # Get recent activity summary
            context = "Recent intelligence activity"
        
        prompt = f"""
Based on the following intelligence context, predict emerging patterns:

Context: {context}

Identify:
1. Early signals of emerging trends
2. Potential future developments
3. Entities that may become more prominent
4. Geographic areas of increasing activity

Provide predictions with confidence scores.
"""
        
        response = await self._llm_model_func(
            prompt,
            system_prompt="You are an expert at predictive intelligence analysis and pattern recognition."
        )
        
        return self._parse_prediction_response(response)
    
    def _parse_prediction_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse prediction response"""
        # Simplified - enhance with structured output
        return []
    
    async def analyze_information_gaps(
        self,
        entity: str
    ) -> Dict[str, Any]:
        """
        Identify information gaps in entity coverage
        """
        # Query what we know
        known_info = await self.query(
            f"What information do we have about {entity}?",
            mode=QueryMode.GLOBAL
        )
        
        prompt = f"""
Analyze information gaps for entity: {entity}

Known information:
{known_info['answer']}

Identify:
1. Critical missing information
2. Contradictions in available information
3. Areas needing verification
4. Suggested collection priorities

Provide a structured gap analysis.
"""
        
        response = await self._llm_model_func(
            prompt,
            system_prompt="You are an expert at intelligence gap analysis."
        )
        
        return {
            "entity": entity,
            "known_info_summary": known_info['answer'][:500],
            "gap_analysis": response,
            "collection_priorities": []
        }
