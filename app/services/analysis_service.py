"""
Analysis Service
Narrative detection, gap analysis, and predictive alerts
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from ..models.schemas import (
    NarrativePattern, PredictiveAlert, Entity, Document, QueryMode
)
from ..core.config import settings
from .lightrag_service import OSINTLightRAG
from .entity_resolver import EntityResolver
from .temporal_analyzer import TemporalAnalyzer
from .geographic_analyzer import GeographicAnalyzer
from .credibility_scorer import CredibilityScorer


class AnalysisService:
    """
    Advanced analysis capabilities
    - Narrative detection (coordinated information campaigns)
    - Gap analysis (identify missing intelligence)
    - Predictive alerts (emerging patterns)
    """
    
    def __init__(
        self,
        lightrag: OSINTLightRAG,
        entity_resolver: EntityResolver,
        temporal_analyzer: TemporalAnalyzer,
        geo_analyzer: GeographicAnalyzer,
        credibility_scorer: CredibilityScorer
    ):
        self.lightrag = lightrag
        self.entity_resolver = entity_resolver
        self.temporal = temporal_analyzer
        self.geo = geo_analyzer
        self.credibility = credibility_scorer
        self.detected_narratives: List[NarrativePattern] = []
        self.active_alerts: List[PredictiveAlert] = []
        
    async def detect_coordinated_narratives(
        self,
        entity_ids: List[str],
        time_window_days: int = None
    ) -> List[NarrativePattern]:
        """
        Detect coordinated narratives across sources
        Identifies information campaigns and coordinated messaging
        """
        time_window_days = time_window_days or settings.NARRATIVE_DETECTION_WINDOW_DAYS
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_window_days)
        
        narratives = []
        
        # Analyze temporal patterns for coordination
        frequency_data = self.temporal.analyze_event_frequency(entity_ids, time_window_days)
        concurrent_events = self.temporal.find_concurrent_events(entity_ids, time_window_hours=6)
        
        # Look for unusual coordination patterns
        for concurrent_group in concurrent_events:
            if concurrent_group["entity_count"] < 2:
                continue
            
            entities_involved = list(concurrent_group["entities_involved"])
            
            # Use LightRAG to analyze narrative themes
            narrative_analysis = await self.lightrag.find_narrative_patterns(
                entities_involved,
                time_window_days
            )
            
            # Calculate coordination score
            coordination_score = self._calculate_coordination_score(
                concurrent_group,
                frequency_data
            )
            
            if coordination_score >= 0.6:  # Threshold for significant coordination
                # Build temporal pattern
                temporal_pattern = {}
                for event in concurrent_group["events"]:
                    timestamp_key = event["timestamp"].strftime("%Y-%m-%d %H:00")
                    temporal_pattern[timestamp_key] = temporal_pattern.get(timestamp_key, 0) + 1
                
                # Get sources involved
                sources = set()
                for entity_id in entities_involved:
                    entity = self.entity_resolver.get_entity_by_id(entity_id)
                    if entity:
                        sources.update(entity.sources)
                
                narrative = NarrativePattern(
                    narrative_theme=f"Coordinated activity involving {len(entities_involved)} entities",
                    entities_involved=entities_involved,
                    sources=list(sources),
                    coordination_score=coordination_score,
                    temporal_pattern=temporal_pattern,
                    first_detected=concurrent_group["center_time"],
                    last_updated=datetime.utcnow()
                )
                
                narratives.append(narrative)
                self.detected_narratives.append(narrative)
        
        return narratives
    
    def _calculate_coordination_score(
        self,
        concurrent_group: Dict[str, Any],
        frequency_data: Dict[str, Any]
    ) -> float:
        """
        Calculate how coordinated a group of events appears
        Higher score = more likely to be coordinated
        """
        # Factors:
        # 1. Temporal proximity (how close in time)
        # 2. Number of entities involved
        # 3. Deviation from normal activity patterns
        
        score = 0.0
        
        # Temporal proximity (tighter = more coordinated)
        time_span = concurrent_group.get("time_span_hours", 24)
        temporal_score = max(0, 1 - (time_span / 24))  # Normalized to 24 hours
        score += temporal_score * 0.4
        
        # Entity count (more entities = potentially more coordinated)
        entity_count = concurrent_group.get("entity_count", 1)
        entity_score = min(1.0, entity_count / 5)  # Normalize to 5 entities
        score += entity_score * 0.3
        
        # Activity anomaly (unusual spike = more suspicious)
        event_count = concurrent_group.get("event_count", 1)
        anomaly_score = min(1.0, event_count / 10)  # Normalize to 10 events
        score += anomaly_score * 0.3
        
        return min(1.0, score)
    
    async def analyze_information_gaps(
        self,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Identify information gaps and intelligence collection priorities
        """
        entity = self.entity_resolver.get_entity_by_id(entity_id)
        if not entity:
            return {"error": "Entity not found"}
        
        # Use LightRAG gap analysis
        gap_analysis = await self.lightrag.analyze_information_gaps(entity.name)
        
        # Analyze coverage
        gaps = {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "gaps": [],
            "priorities": []
        }
        
        # Check temporal gaps
        events = self.temporal.reconstruct_timeline(entity_id)
        if events:
            # Look for large time gaps between events
            for i in range(1, len(events)):
                time_gap = (events[i]["timestamp"] - events[i-1]["timestamp"]).days
                if time_gap > 30:  # More than 30 days
                    gaps["gaps"].append({
                        "type": "temporal",
                        "description": f"No activity for {time_gap} days",
                        "start": events[i-1]["timestamp"],
                        "end": events[i]["timestamp"],
                        "severity": "high" if time_gap > 90 else "medium"
                    })
        
        # Check geographic coverage
        locations = self.geo.entity_locations.get(entity_id, [])
        if len(locations) < 2:
            gaps["gaps"].append({
                "type": "geographic",
                "description": "Limited geographic information",
                "severity": "medium"
            })
        
        # Check source diversity
        source_diversity = self.credibility.analyze_source_diversity(entity.sources)
        if source_diversity["total_sources"] < 3:
            gaps["gaps"].append({
                "type": "source_diversity",
                "description": "Limited source diversity",
                "severity": "high"
            })
        
        # Generate collection priorities
        gaps["priorities"] = self._generate_collection_priorities(gaps["gaps"], entity)
        
        # Add LLM-generated insights
        gaps["llm_analysis"] = gap_analysis.get("gap_analysis", "")
        
        return gaps
    
    def _generate_collection_priorities(
        self,
        gaps: List[Dict[str, Any]],
        entity: Entity
    ) -> List[Dict[str, Any]]:
        """Generate prioritized intelligence collection requirements"""
        priorities = []
        
        for gap in gaps:
            if gap["severity"] == "high":
                priority = {
                    "priority_level": "high",
                    "gap_type": gap["type"],
                    "description": gap["description"],
                    "suggested_actions": []
                }
                
                if gap["type"] == "temporal":
                    priority["suggested_actions"] = [
                        "Review archived sources for the time period",
                        "Check alternative sources active during gap",
                        "Conduct targeted searches for entity during period"
                    ]
                elif gap["type"] == "geographic":
                    priority["suggested_actions"] = [
                        "Search for location mentions in documents",
                        "Review public records for address information",
                        "Check social media for location tags"
                    ]
                elif gap["type"] == "source_diversity":
                    priority["suggested_actions"] = [
                        "Expand to additional source types",
                        "Cross-reference with public records",
                        "Monitor social media channels"
                    ]
                
                priorities.append(priority)
        
        return priorities
    
    async def generate_predictive_alerts(
        self,
        entity_ids: Optional[List[str]] = None
    ) -> List[PredictiveAlert]:
        """
        Generate predictive alerts for emerging patterns
        Uses multiple signals to predict future developments
        """
        alerts = []
        
        entity_ids = entity_ids or list(self.entity_resolver.entity_index.keys())
        
        for entity_id in entity_ids[:50]:  # Limit to avoid overwhelming
            # Analyze velocity (acceleration of activity)
            velocity = self.temporal.calculate_event_velocity(entity_id)
            
            if velocity and velocity["velocity"] > 0.5:  # Significant increase
                # Get entity details
                entity = self.entity_resolver.get_entity_by_id(entity_id)
                if not entity:
                    continue
                
                # Use LightRAG for pattern prediction
                context = f"Entity {entity.name} showing increased activity: {velocity['trend']}"
                predictions = await self.lightrag.predict_emerging_patterns(context)
                
                # Calculate confidence based on multiple factors
                confidence = self._calculate_prediction_confidence(velocity, entity)
                
                if confidence >= settings.PREDICTIVE_ALERT_THRESHOLD:
                    alert = PredictiveAlert(
                        alert_type="emerging_activity",
                        entities=[entity_id],
                        description=f"Accelerating activity for {entity.name}. "
                                  f"Frequency increased by {velocity['velocity']:.2f} events/day.",
                        confidence=confidence,
                        supporting_evidence=[
                            f"Velocity: {velocity['velocity']:.2f}",
                            f"Trend: {velocity['trend']}",
                            f"Period 1 freq: {velocity['period1_freq']:.2f}",
                            f"Period 2 freq: {velocity['period2_freq']:.2f}"
                        ]
                    )
                    
                    alerts.append(alert)
                    self.active_alerts.append(alert)
        
        # Check for geographic clustering patterns
        geo_clusters = self.geo.find_geographic_clusters(entity_ids)
        for cluster in geo_clusters:
            if cluster.entity_count >= 5:  # Significant cluster
                alert = PredictiveAlert(
                    alert_type="geographic_concentration",
                    entities=cluster.entities,
                    description=f"Geographic cluster of {cluster.entity_count} entities "
                              f"near {cluster.center_location['lat']:.2f}, {cluster.center_location['lon']:.2f}",
                    confidence=min(1.0, cluster.entity_count / 10),
                    supporting_evidence=[
                        f"Entity count: {cluster.entity_count}",
                        f"Radius: {cluster.radius_km} km"
                    ]
                )
                alerts.append(alert)
        
        return alerts
    
    def _calculate_prediction_confidence(
        self,
        velocity: Dict[str, Any],
        entity: Entity
    ) -> float:
        """Calculate confidence score for a prediction"""
        confidence = 0.0
        
        # Velocity magnitude
        vel_mag = abs(velocity.get("velocity", 0))
        confidence += min(0.4, vel_mag / 2)  # Up to 0.4 based on velocity
        
        # Source credibility
        if entity.sources:
            avg_credibility = sum(
                self.credibility.get_source_score(s) for s in entity.sources
            ) / len(entity.sources)
            confidence += avg_credibility * 0.3
        
        # Entity confidence
        confidence += entity.confidence * 0.3
        
        return min(1.0, confidence)
    
    async def cross_verify_claim(
        self,
        claim: str,
        min_sources: int = 3
    ) -> Dict[str, Any]:
        """
        Cross-verify a claim across multiple sources
        """
        # Query for information about the claim
        result = await self.lightrag.query(
            f"Verify this claim and provide sources: {claim}",
            mode=QueryMode.HYBRID,
            only_credible_sources=True
        )
        
        # Detect contradictions
        contradiction = await self.lightrag.detect_contradictions(claim)
        
        # Analyze source diversity
        # (In production, would extract actual source IDs from query results)
        
        verification = {
            "claim": claim,
            "verification_status": "unknown",
            "confidence": 0.5,
            "supporting_sources": [],
            "contradicting_sources": contradiction.get("evidence", []),
            "contradiction_score": contradiction.get("contradiction_score", 0),
            "analysis": result.get("answer", "")
        }
        
        # Determine verification status
        if contradiction["contradiction_score"] > 0.7:
            verification["verification_status"] = "likely_false"
            verification["confidence"] = contradiction["contradiction_score"]
        elif contradiction["contradiction_score"] < 0.3:
            verification["verification_status"] = "likely_true"
            verification["confidence"] = 1 - contradiction["contradiction_score"]
        else:
            verification["verification_status"] = "inconclusive"
            verification["confidence"] = 0.5
        
        return verification
    
    def get_narrative_summary(self) -> Dict[str, Any]:
        """Get summary of detected narratives"""
        return {
            "total_narratives": len(self.detected_narratives),
            "active_narratives": len([
                n for n in self.detected_narratives
                if (datetime.utcnow() - n.last_updated).days < 7
            ]),
            "high_coordination": len([
                n for n in self.detected_narratives
                if n.coordination_score >= 0.8
            ]),
            "narratives": self.detected_narratives[-10:]  # Most recent 10
        }
    
    def get_active_alerts(self, limit: int = 20) -> List[PredictiveAlert]:
        """Get recent active alerts"""
        # Filter to recent alerts (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = [a for a in self.active_alerts if a.created_at >= cutoff]
        
        # Sort by confidence
        recent.sort(key=lambda x: x.confidence, reverse=True)
        
        return recent[:limit]
