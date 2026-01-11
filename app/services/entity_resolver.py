"""
Entity Resolution Service
Resolves entities across multiple sources with different naming conventions
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import asyncio
from datetime import datetime
from difflib import SequenceMatcher
import re
from collections import defaultdict

from ..models.schemas import Entity, EntityResolutionResult
from ..core.config import settings
from .lightrag_service import OSINTLightRAG


class EntityResolver:
    """
    Advanced entity resolution across multiple sources
    Handles:
    - Name variations (John Smith, J. Smith, Smith, John)
    - Aliases and nicknames
    - Fuzzy matching
    - LLM-assisted disambiguation
    """
    
    def __init__(self, lightrag: OSINTLightRAG):
        self.lightrag = lightrag
        self.entity_index: Dict[str, Entity] = {}
        self.alias_map: Dict[str, str] = {}  # alias -> canonical_id
        self.similarity_threshold = 0.85
        
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        # Convert to lowercase
        normalized = name.lower().strip()
        # Remove common titles and suffixes
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'jr', 'sr', 'ii', 'iii']
        words = normalized.split()
        words = [w.rstrip('.,') for w in words if w.rstrip('.,') not in titles]
        return ' '.join(words)
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Check if one is substring of other (initials case)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # Common words ratio
        if words1 and words2:
            common = words1.intersection(words2)
            ratio = len(common) / max(len(words1), len(words2))
            if ratio > 0.5:
                return 0.7 + (ratio * 0.3)
        
        # Sequence matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _extract_initials(self, name: str) -> str:
        """Extract initials from name"""
        words = self._normalize_name(name).split()
        return ''.join([w[0] for w in words if w])
    
    async def resolve_entity(
        self,
        entity: Entity,
        use_llm: bool = True
    ) -> EntityResolutionResult:
        """
        Resolve an entity against existing entities
        Returns canonical entity ID and merge information
        """
        # Check exact matches in alias map
        if entity.name in self.alias_map:
            canonical_id = self.alias_map[entity.name]
            return EntityResolutionResult(
                canonical_entity_id=canonical_id,
                merged_entities=[entity.name],
                confidence=1.0,
                resolution_method="exact_match"
            )
        
        # Find similar entities
        candidates = []
        for existing_id, existing_entity in self.entity_index.items():
            if existing_entity.entity_type != entity.entity_type:
                continue
                
            # Check name similarity
            similarity = self._calculate_similarity(entity.name, existing_entity.name)
            if similarity >= self.similarity_threshold:
                candidates.append((existing_id, existing_entity, similarity))
            
            # Check aliases
            for alias in existing_entity.aliases:
                similarity = self._calculate_similarity(entity.name, alias)
                if similarity >= self.similarity_threshold:
                    candidates.append((existing_id, existing_entity, similarity))
        
        if not candidates:
            # New entity
            entity_id = self._generate_entity_id(entity)
            self.entity_index[entity_id] = entity
            self.alias_map[entity.name] = entity_id
            
            return EntityResolutionResult(
                canonical_entity_id=entity_id,
                merged_entities=[entity.name],
                confidence=1.0,
                resolution_method="new_entity"
            )
        
        # Sort by similarity
        candidates.sort(key=lambda x: x[2], reverse=True)
        best_match = candidates[0]
        
        # If high confidence, merge immediately
        if best_match[2] >= 0.95:
            return await self._merge_entities(entity, best_match[0], best_match[1], best_match[2])
        
        # Use LLM for disambiguation if enabled
        if use_llm and len(candidates) > 1:
            llm_result = await self._llm_disambiguation(entity, candidates[:3])
            if llm_result:
                return llm_result
        
        # Default to best match
        return await self._merge_entities(entity, best_match[0], best_match[1], best_match[2])
    
    async def _merge_entities(
        self,
        new_entity: Entity,
        canonical_id: str,
        canonical_entity: Entity,
        confidence: float
    ) -> EntityResolutionResult:
        """Merge new entity into canonical entity"""
        # Update canonical entity
        if new_entity.name not in canonical_entity.aliases:
            canonical_entity.aliases.append(new_entity.name)
        
        # Merge attributes
        for key, value in new_entity.attributes.items():
            if key not in canonical_entity.attributes:
                canonical_entity.attributes[key] = value
        
        # Merge sources
        for source in new_entity.sources:
            if source not in canonical_entity.sources:
                canonical_entity.sources.append(source)
        
        # Update timestamps
        if new_entity.first_mentioned < canonical_entity.first_mentioned:
            canonical_entity.first_mentioned = new_entity.first_mentioned
        if new_entity.last_mentioned > canonical_entity.last_mentioned:
            canonical_entity.last_mentioned = new_entity.last_mentioned
        
        # Update alias map
        self.alias_map[new_entity.name] = canonical_id
        
        return EntityResolutionResult(
            canonical_entity_id=canonical_id,
            merged_entities=[new_entity.name, canonical_entity.name],
            confidence=confidence,
            resolution_method="similarity_merge"
        )
    
    async def _llm_disambiguation(
        self,
        entity: Entity,
        candidates: List[Tuple[str, Entity, float]]
    ) -> Optional[EntityResolutionResult]:
        """Use LLM to disambiguate between candidate entities"""
        candidate_descriptions = []
        for i, (eid, e, score) in enumerate(candidates):
            desc = f"{i+1}. {e.name} (type: {e.entity_type}, aliases: {', '.join(e.aliases[:3])}, "
            desc += f"attributes: {list(e.attributes.keys())[:3]}, similarity: {score:.2f})"
            candidate_descriptions.append(desc)
        
        prompt = f"""
Determine if the following entity matches any of the candidates:

New Entity:
- Name: {entity.name}
- Type: {entity.entity_type}
- Attributes: {list(entity.attributes.keys())}
- Context: {entity.attributes.get('context', 'N/A')}

Candidates:
{chr(10).join(candidate_descriptions)}

Are any of these candidates the same entity as the new entity?
Respond with:
- The candidate number if there's a match (1, 2, or 3)
- "NEW" if this is a distinct new entity
- Include confidence score (0.0 to 1.0)

Format: CANDIDATE_NUMBER|CONFIDENCE or NEW|CONFIDENCE
"""
        
        try:
            response = await self.lightrag._llm_model_func(
                prompt,
                system_prompt="You are an expert at entity resolution and disambiguation."
            )
            
            # Parse response
            parts = response.strip().upper().split('|')
            if len(parts) == 2:
                decision, confidence = parts[0], float(parts[1])
                
                if decision == "NEW":
                    entity_id = self._generate_entity_id(entity)
                    self.entity_index[entity_id] = entity
                    return EntityResolutionResult(
                        canonical_entity_id=entity_id,
                        merged_entities=[entity.name],
                        confidence=confidence,
                        resolution_method="llm_new"
                    )
                else:
                    # Extract candidate number
                    idx = int(decision) - 1
                    if 0 <= idx < len(candidates):
                        canonical_id, canonical_entity, _ = candidates[idx]
                        return await self._merge_entities(
                            entity, canonical_id, canonical_entity, confidence
                        )
        except Exception as e:
            print(f"LLM disambiguation error: {e}")
        
        return None
    
    def _generate_entity_id(self, entity: Entity) -> str:
        """Generate unique entity ID"""
        normalized = self._normalize_name(entity.name)
        base_id = normalized.replace(' ', '_')
        entity_id = f"{entity.entity_type}_{base_id}"
        
        # Ensure uniqueness
        counter = 1
        original_id = entity_id
        while entity_id in self.entity_index:
            entity_id = f"{original_id}_{counter}"
            counter += 1
        
        return entity_id
    
    async def resolve_batch(
        self,
        entities: List[Entity],
        use_llm: bool = True
    ) -> List[EntityResolutionResult]:
        """Resolve multiple entities in batch"""
        results = []
        for entity in entities:
            result = await self.resolve_entity(entity, use_llm)
            results.append(result)
        return results
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get entity by canonical ID"""
        return self.entity_index.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get entity by name (checks aliases)"""
        canonical_id = self.alias_map.get(name)
        if canonical_id:
            return self.entity_index.get(canonical_id)
        return None
    
    def get_all_entities(self) -> List[Entity]:
        """Get all canonical entities"""
        return list(self.entity_index.values())
    
    def get_entity_network(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get network of related entities"""
        # This would integrate with the knowledge graph
        # Simplified implementation
        entity = self.get_entity_by_id(entity_id)
        if not entity:
            return {}
        
        return {
            "entity": entity,
            "related_entities": [],
            "depth": depth
        }
