"""
Dependency injection for services
Singleton pattern for service instances
"""

from functools import lru_cache

from ..services.lightrag_service import OSINTLightRAG
from ..services.entity_resolver import EntityResolver
from ..services.credibility_scorer import CredibilityScorer
from ..services.ingestion_service import DataIngestionService
from ..services.temporal_analyzer import TemporalAnalyzer
from ..services.geographic_analyzer import GeographicAnalyzer
from ..services.analysis_service import AnalysisService
from .config import settings


# Singleton instances
_lightrag_instance = None
_entity_resolver_instance = None
_credibility_scorer_instance = None
_ingestion_service_instance = None
_temporal_analyzer_instance = None
_geo_analyzer_instance = None
_analysis_service_instance = None


def get_lightrag_service() -> OSINTLightRAG:
    """Get LightRAG service instance"""
    global _lightrag_instance
    if _lightrag_instance is None:
        _lightrag_instance = OSINTLightRAG(settings.WORKING_DIR)
    return _lightrag_instance


def get_entity_resolver() -> EntityResolver:
    """Get entity resolver instance"""
    global _entity_resolver_instance
    if _entity_resolver_instance is None:
        lightrag = get_lightrag_service()
        _entity_resolver_instance = EntityResolver(lightrag)
    return _entity_resolver_instance


def get_credibility_scorer() -> CredibilityScorer:
    """Get credibility scorer instance"""
    global _credibility_scorer_instance
    if _credibility_scorer_instance is None:
        _credibility_scorer_instance = CredibilityScorer()
    return _credibility_scorer_instance


def get_temporal_analyzer() -> TemporalAnalyzer:
    """Get temporal analyzer instance"""
    global _temporal_analyzer_instance
    if _temporal_analyzer_instance is None:
        _temporal_analyzer_instance = TemporalAnalyzer()
    return _temporal_analyzer_instance


def get_geo_analyzer() -> GeographicAnalyzer:
    """Get geographic analyzer instance"""
    global _geo_analyzer_instance
    if _geo_analyzer_instance is None:
        _geo_analyzer_instance = GeographicAnalyzer()
    return _geo_analyzer_instance


def get_ingestion_service() -> DataIngestionService:
    """Get ingestion service instance"""
    global _ingestion_service_instance
    if _ingestion_service_instance is None:
        lightrag = get_lightrag_service()
        entity_resolver = get_entity_resolver()
        credibility_scorer = get_credibility_scorer()
        _ingestion_service_instance = DataIngestionService(
            lightrag, entity_resolver, credibility_scorer
        )
    return _ingestion_service_instance


def get_analysis_service() -> AnalysisService:
    """Get analysis service instance"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        lightrag = get_lightrag_service()
        entity_resolver = get_entity_resolver()
        temporal = get_temporal_analyzer()
        geo = get_geo_analyzer()
        credibility = get_credibility_scorer()
        _analysis_service_instance = AnalysisService(
            lightrag, entity_resolver, temporal, geo, credibility
        )
    return _analysis_service_instance


def reset_services():
    """Reset all service instances (for testing)"""
    global _lightrag_instance, _entity_resolver_instance, _credibility_scorer_instance
    global _ingestion_service_instance, _temporal_analyzer_instance
    global _geo_analyzer_instance, _analysis_service_instance
    
    _lightrag_instance = None
    _entity_resolver_instance = None
    _credibility_scorer_instance = None
    _ingestion_service_instance = None
    _temporal_analyzer_instance = None
    _geo_analyzer_instance = None
    _analysis_service_instance = None
