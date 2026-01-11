"""
Source Credibility Scoring System
Dynamically evaluates source reliability based on multiple factors
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import math

from ..models.schemas import Source, SourceType, CredibilityLevel, Document
from ..core.config import settings


class CredibilityScorer:
    """
    Multi-factor source credibility scoring system
    Factors:
    - Historical accuracy
    - Cross-verification with other sources
    - Update frequency and consistency
    - Source type baseline
    - Domain expertise
    - Editorial standards indicators
    """

    def __init__(self):
        self.source_history: Dict[str, Dict[str, Any]] = {}
        self.sources: Dict[str, Source] = {}  # Store registered sources
        
        # Base credibility by source type
        self.type_baselines = {
            SourceType.GOVERNMENT: 0.8,
            SourceType.ACADEMIC: 0.85,
            SourceType.NEWS: 0.6,
            SourceType.SOCIAL_MEDIA: 0.3,
            SourceType.FORUM: 0.25,
            SourceType.BLOG: 0.4,
            SourceType.PUBLIC_RECORDS: 0.9,
            SourceType.OTHER: 0.5
        }
        
    def initialize_source(self, source: Source) -> float:
        """Initialize credibility score for a new source"""
        base_score = self.type_baselines.get(source.type, settings.DEFAULT_SOURCE_CREDIBILITY)
        
        # Adjust based on URL domain if available
        if source.url:
            domain_adjustment = self._assess_domain(str(source.url))
            base_score = (base_score + domain_adjustment) / 2
        
        self.source_history[source.id] = {
            "initial_score": base_score,
            "current_score": base_score,
            "documents_published": 0,
            "verified_accurate": 0,
            "verified_inaccurate": 0,
            "cross_verified": 0,
            "contradicted": 0,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "consistency_scores": []
        }
        
        return base_score
    
    def _assess_domain(self, url: str) -> float:
        """Assess credibility based on domain characteristics"""
        url_lower = url.lower()
        
        # Known high-credibility domains
        high_cred_indicators = ['.gov', '.edu', '.org', 'reuters', 'ap.org', 'bbc']
        for indicator in high_cred_indicators:
            if indicator in url_lower:
                return 0.9
        
        # Medium credibility indicators
        med_cred_indicators = ['.com', 'news', 'times', 'post']
        for indicator in med_cred_indicators:
            if indicator in url_lower:
                return 0.6
        
        # Low credibility indicators
        low_cred_indicators = ['blog', 'tumblr', 'wordpress', 'medium']
        for indicator in low_cred_indicators:
            if indicator in url_lower:
                return 0.4
        
        return 0.5
    
    def update_score_on_verification(
        self,
        source_id: str,
        was_accurate: bool,
        verification_confidence: float = 1.0
    ) -> float:
        """Update score when a claim is verified or debunked"""
        if source_id not in self.source_history:
            return settings.DEFAULT_SOURCE_CREDIBILITY
        
        history = self.source_history[source_id]
        current_score = history["current_score"]
        
        if was_accurate:
            history["verified_accurate"] += 1
            # Increase score (diminishing returns)
            adjustment = 0.1 * verification_confidence * math.exp(-history["verified_accurate"] / 10)
            new_score = min(1.0, current_score + adjustment)
        else:
            history["verified_inaccurate"] += 1
            # Decrease score (stronger penalty)
            adjustment = 0.15 * verification_confidence * math.exp(-history["verified_inaccurate"] / 5)
            new_score = max(0.0, current_score - adjustment)
        
        history["current_score"] = new_score
        history["last_updated"] = datetime.utcnow()
        
        return new_score
    
    def update_score_on_cross_verification(
        self,
        source_id: str,
        was_corroborated: bool,
        num_corroborating_sources: int = 1
    ) -> float:
        """Update score based on cross-verification with other sources"""
        if source_id not in self.source_history:
            return settings.DEFAULT_SOURCE_CREDIBILITY
        
        history = self.source_history[source_id]
        current_score = history["current_score"]
        
        # Weight by number of corroborating sources
        weight = min(1.0, num_corroborating_sources / 3.0)
        
        if was_corroborated:
            history["cross_verified"] += 1
            adjustment = 0.05 * weight
            new_score = min(1.0, current_score + adjustment)
        else:
            history["contradicted"] += 1
            adjustment = 0.08 * weight
            new_score = max(0.0, current_score - adjustment)
        
        history["current_score"] = new_score
        history["last_updated"] = datetime.utcnow()
        
        return new_score
    
    def update_score_on_consistency(
        self,
        source_id: str,
        consistency_score: float
    ) -> float:
        """Update based on consistency of reporting over time"""
        if source_id not in self.source_history:
            return settings.DEFAULT_SOURCE_CREDIBILITY
        
        history = self.source_history[source_id]
        history["consistency_scores"].append(consistency_score)
        
        # Keep only recent consistency scores
        if len(history["consistency_scores"]) > 20:
            history["consistency_scores"] = history["consistency_scores"][-20:]
        
        # Calculate average consistency
        avg_consistency = sum(history["consistency_scores"]) / len(history["consistency_scores"])
        
        # Adjust current score based on consistency
        current_score = history["current_score"]
        target_score = (current_score + avg_consistency) / 2
        
        # Gradual adjustment
        new_score = current_score * 0.9 + target_score * 0.1
        history["current_score"] = new_score
        history["last_updated"] = datetime.utcnow()
        
        return new_score
    
    def calculate_weighted_edge_score(
        self,
        source_ids: List[str],
        base_relationship_strength: float = 1.0
    ) -> float:
        """
        Calculate credibility-weighted score for a relationship/edge
        Uses harmonic mean for conservative weighting
        """
        if not source_ids:
            return 0.0
        
        scores = []
        for source_id in source_ids:
            if source_id in self.source_history:
                scores.append(self.source_history[source_id]["current_score"])
            else:
                scores.append(settings.DEFAULT_SOURCE_CREDIBILITY)
        
        # Harmonic mean (penalizes low scores more)
        harmonic_mean = len(scores) / sum(1/s if s > 0 else 1/0.01 for s in scores)
        
        return harmonic_mean * base_relationship_strength
    
    def get_credibility_level(self, score: float) -> CredibilityLevel:
        """Convert numeric score to credibility level"""
        if score >= 0.9:
            return CredibilityLevel.VERIFIED
        elif score >= 0.7:
            return CredibilityLevel.HIGH
        elif score >= 0.5:
            return CredibilityLevel.MEDIUM
        elif score >= 0.3:
            return CredibilityLevel.LOW
        elif score >= 0.15:
            return CredibilityLevel.UNVERIFIED
        else:
            return CredibilityLevel.DISPUTED
    
    def get_source_score(self, source_id: str) -> float:
        """Get current credibility score for a source"""
        if source_id in self.source_history:
            return self.source_history[source_id]["current_score"]
        return settings.DEFAULT_SOURCE_CREDIBILITY
    
    def get_source_stats(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a source"""
        if source_id not in self.source_history:
            return None
        
        history = self.source_history[source_id]
        total_verifications = history["verified_accurate"] + history["verified_inaccurate"]
        
        stats = {
            "source_id": source_id,
            "current_score": history["current_score"],
            "initial_score": history["initial_score"],
            "credibility_level": self.get_credibility_level(history["current_score"]).value,
            "total_documents": history["documents_published"],
            "accuracy_rate": (
                history["verified_accurate"] / total_verifications 
                if total_verifications > 0 else None
            ),
            "cross_verification_rate": (
                history["cross_verified"] / (history["cross_verified"] + history["contradicted"])
                if (history["cross_verified"] + history["contradicted"]) > 0 else None
            ),
            "average_consistency": (
                sum(history["consistency_scores"]) / len(history["consistency_scores"])
                if history["consistency_scores"] else None
            ),
            "age_days": (datetime.utcnow() - history["created_at"]).days,
            "last_updated": history["last_updated"]
        }
        
        return stats
    
    def rank_sources(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """Rank multiple sources by credibility"""
        ranked = []
        for source_id in source_ids:
            score = self.get_source_score(source_id)
            stats = self.get_source_stats(source_id)
            ranked.append({
                "source_id": source_id,
                "score": score,
                "stats": stats
            })
        
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
    
    def filter_credible_sources(
        self,
        source_ids: List[str],
        min_score: float = None
    ) -> List[str]:
        """Filter sources by minimum credibility score"""
        min_score = min_score or settings.MIN_CREDIBILITY_SCORE
        
        return [
            source_id for source_id in source_ids
            if self.get_source_score(source_id) >= min_score
        ]
    
    def analyze_source_diversity(self, source_ids: List[str]) -> Dict[str, Any]:
        """Analyze diversity of source types and credibility"""
        type_counts = defaultdict(int)
        credibility_distribution = defaultdict(int)
        scores = []

        for source_id in source_ids:
            score = self.get_source_score(source_id)
            scores.append(score)
            level = self.get_credibility_level(score)
            credibility_distribution[level.value] += 1

        return {
            "total_sources": len(source_ids),
            "average_credibility": sum(scores) / len(scores) if scores else 0,
            "credibility_distribution": dict(credibility_distribution),
            "diversity_score": len(set(scores)) / len(scores) if scores else 0
        }

    def register_source(self, source: Source) -> Source:
        """Register a new source and initialize its credibility tracking"""
        import uuid

        # Generate ID if not provided
        if not source.id:
            source.id = str(uuid.uuid4())

        # Calculate initial credibility score
        initial_score = self.initialize_source(source)

        # Update source with calculated credibility
        source.credibility_score = initial_score
        source.credibility_level = self.get_credibility_level(initial_score)
        source.first_seen = datetime.utcnow()
        source.last_updated = datetime.utcnow()

        # Store the source
        self.sources[source.id] = source

        return source

    def get_source(self, source_id: str) -> Optional[Source]:
        """Get a registered source by ID"""
        return self.sources.get(source_id)

    def get_all_sources(self) -> List[Source]:
        """Get all registered sources"""
        return list(self.sources.values())

    def update_source(self, source_id: str, updates: Dict[str, Any]) -> Optional[Source]:
        """Update a registered source"""
        if source_id not in self.sources:
            return None

        source = self.sources[source_id]
        for key, value in updates.items():
            if hasattr(source, key) and key not in ('id', 'first_seen'):
                setattr(source, key, value)

        source.last_updated = datetime.utcnow()
        return source

    def delete_source(self, source_id: str) -> bool:
        """Delete a registered source"""
        if source_id in self.sources:
            del self.sources[source_id]
            if source_id in self.source_history:
                del self.source_history[source_id]
            return True
        return False
