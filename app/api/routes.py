"""
FastAPI Routers for OSINT Platform
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..models.schemas import (
    Source, IngestRequest, QueryRequest, QueryResponse,
    Entity, NarrativePattern, PredictiveAlert, GeoCluster
)
from ..core.dependencies import (
    get_ingestion_service,
    get_lightrag_service,
    get_entity_resolver,
    get_analysis_service,
    get_temporal_analyzer,
    get_geo_analyzer
)


router = APIRouter()


# Ingestion Endpoints
@router.post("/ingest/batch", tags=["Ingestion"])
async def ingest_batch(request: IngestRequest):
    """Ingest a batch of documents from a source"""
    ingestion = get_ingestion_service()
    result = await ingestion.ingest_batch(request)
    return result


@router.post("/ingest/rss", tags=["Ingestion"])
async def ingest_from_rss(
    source: Source,
    feed_url: str,
    max_items: int = 50
):
    """Ingest documents from an RSS/Atom feed"""
    ingestion = get_ingestion_service()
    result = await ingestion.ingest_from_rss(source, feed_url, max_items)
    return result


@router.post("/ingest/web", tags=["Ingestion"])
async def ingest_from_web(
    source: Source,
    url: str
):
    """Scrape and ingest content from a web page"""
    ingestion = get_ingestion_service()
    result = await ingestion.ingest_from_web(source, url)
    return result


# Query Endpoints
@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_knowledge(request: QueryRequest):
    """Query the knowledge graph"""
    lightrag = get_lightrag_service()
    await lightrag.initialize()
    
    start_time = datetime.utcnow()
    result = await lightrag.query(
        request.query,
        mode=request.mode,
        only_credible_sources=request.only_credible_sources,
        min_credibility=request.min_credibility
    )
    execution_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Get related entities (simplified)
    entity_resolver = get_entity_resolver()
    entities = entity_resolver.get_all_entities()[:10]
    
    return QueryResponse(
        query=request.query,
        answer=result["answer"],
        sources=[],
        entities=entities,
        confidence=0.8,
        execution_time=execution_time
    )


# Entity Endpoints
@router.get("/entities", tags=["Entities"])
async def list_entities(
    limit: int = Query(50, ge=1, le=500),
    entity_type: Optional[str] = None
):
    """List all entities"""
    resolver = get_entity_resolver()
    entities = resolver.get_all_entities()
    
    if entity_type:
        entities = [e for e in entities if e.entity_type == entity_type]
    
    return {
        "total": len(entities),
        "entities": entities[:limit]
    }


@router.get("/entities/{entity_id}", tags=["Entities"])
async def get_entity(entity_id: str):
    """Get entity details"""
    resolver = get_entity_resolver()
    entity = resolver.get_entity_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity


@router.get("/entities/{entity_id}/network", tags=["Entities"])
async def get_entity_network(
    entity_id: str,
    depth: int = Query(1, ge=1, le=3)
):
    """Get entity relationship network"""
    resolver = get_entity_resolver()
    network = resolver.get_entity_network(entity_id, depth)
    
    if not network:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return network


# Analysis Endpoints
@router.post("/analysis/narratives", tags=["Analysis"])
async def detect_narratives(
    entity_ids: List[str],
    time_window_days: Optional[int] = None
):
    """Detect coordinated narratives"""
    analysis = get_analysis_service()
    narratives = await analysis.detect_coordinated_narratives(
        entity_ids,
        time_window_days
    )
    
    return {
        "narratives_detected": len(narratives),
        "narratives": narratives
    }


@router.get("/analysis/narratives/summary", tags=["Analysis"])
async def get_narrative_summary():
    """Get summary of detected narratives"""
    analysis = get_analysis_service()
    return analysis.get_narrative_summary()


@router.get("/analysis/gaps/{entity_id}", tags=["Analysis"])
async def analyze_gaps(entity_id: str):
    """Analyze information gaps for an entity"""
    analysis = get_analysis_service()
    gaps = await analysis.analyze_information_gaps(entity_id)
    return gaps


@router.post("/analysis/verify", tags=["Analysis"])
async def verify_claim(
    claim: str,
    min_sources: int = Query(3, ge=1, le=10)
):
    """Cross-verify a claim"""
    analysis = get_analysis_service()
    verification = await analysis.cross_verify_claim(claim, min_sources)
    return verification


@router.get("/analysis/alerts", tags=["Analysis"])
async def get_alerts(limit: int = Query(20, ge=1, le=100)):
    """Get active predictive alerts"""
    analysis = get_analysis_service()
    alerts = analysis.get_active_alerts(limit)
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts
    }


@router.post("/analysis/alerts/generate", tags=["Analysis"])
async def generate_alerts(entity_ids: Optional[List[str]] = None):
    """Generate new predictive alerts"""
    analysis = get_analysis_service()
    alerts = await analysis.generate_predictive_alerts(entity_ids)
    
    return {
        "alerts_generated": len(alerts),
        "alerts": alerts
    }


# Temporal Analysis Endpoints
@router.get("/temporal/timeline/{entity_id}", tags=["Temporal"])
async def get_timeline(
    entity_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get entity timeline"""
    temporal = get_temporal_analyzer()
    timeline = temporal.reconstruct_timeline(entity_id, start_date, end_date)
    
    return {
        "entity_id": entity_id,
        "event_count": len(timeline),
        "timeline": timeline
    }


@router.get("/temporal/clusters/{entity_id}", tags=["Temporal"])
async def get_temporal_clusters(entity_id: str):
    """Get temporal activity clusters"""
    temporal = get_temporal_analyzer()
    clusters = temporal.get_temporal_clusters(entity_id)
    
    return {
        "entity_id": entity_id,
        "cluster_count": len(clusters),
        "clusters": clusters
    }


@router.get("/temporal/anomalies/{entity_id}", tags=["Temporal"])
async def get_temporal_anomalies(entity_id: str):
    """Detect temporal anomalies"""
    temporal = get_temporal_analyzer()
    anomalies = temporal.detect_temporal_anomalies(entity_id)
    
    return {
        "entity_id": entity_id,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies
    }


@router.post("/temporal/concurrent", tags=["Temporal"])
async def find_concurrent_events(
    entity_ids: List[str],
    time_window_hours: int = Query(24, ge=1, le=168)
):
    """Find concurrent events across entities"""
    temporal = get_temporal_analyzer()
    concurrent = temporal.find_concurrent_events(entity_ids, time_window_hours)
    
    return {
        "concurrent_groups": len(concurrent),
        "groups": concurrent
    }


# Geographic Analysis Endpoints
@router.post("/geographic/clusters", tags=["Geographic"])
async def find_geo_clusters(
    entity_ids: List[str],
    radius_km: Optional[float] = None
):
    """Find geographic clusters"""
    geo = get_geo_analyzer()
    clusters = geo.find_geographic_clusters(entity_ids, radius_km)
    
    return {
        "cluster_count": len(clusters),
        "clusters": clusters
    }


@router.get("/geographic/movement/{entity_id}", tags=["Geographic"])
async def analyze_movement(entity_id: str):
    """Analyze entity movement patterns"""
    geo = get_geo_analyzer()
    movement = geo.analyze_entity_movement(entity_id)
    
    if not movement:
        raise HTTPException(status_code=404, detail="Insufficient location data")
    
    return movement


@router.post("/geographic/nearby", tags=["Geographic"])
async def find_nearby_entities(
    latitude: float,
    longitude: float,
    radius_km: float,
    entity_ids: Optional[List[str]] = None
):
    """Find entities near a location"""
    geo = get_geo_analyzer()
    nearby = geo.find_entities_near_location(
        latitude, longitude, radius_km, entity_ids
    )
    
    return {
        "location": {"lat": latitude, "lon": longitude},
        "radius_km": radius_km,
        "entities_found": len(nearby),
        "entities": nearby
    }


@router.post("/geographic/hotspots", tags=["Geographic"])
async def detect_hotspots(
    entity_ids: List[str],
    grid_size_km: float = Query(50, ge=1, le=500)
):
    """Detect geographic hotspots"""
    geo = get_geo_analyzer()
    hotspots = geo.detect_geographic_hotspots(entity_ids, grid_size_km)
    
    return {
        "hotspot_count": len(hotspots),
        "hotspots": hotspots
    }


# Source Management Endpoints
@router.post("/sources", tags=["Sources"])
async def register_source(source: Source):
    """Register a new data source"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    registered_source = scorer.register_source(source)

    return registered_source


@router.get("/sources", tags=["Sources"])
async def list_sources():
    """List all registered sources"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    sources = scorer.get_all_sources()

    return {
        "total": len(sources),
        "sources": sources
    }


@router.get("/sources/{source_id}", tags=["Sources"])
async def get_source(source_id: str):
    """Get a specific source by ID"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    source = scorer.get_source(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.delete("/sources/{source_id}", tags=["Sources"])
async def delete_source(source_id: str):
    """Delete a source"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    deleted = scorer.delete_source(source_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")

    return {"message": "Source deleted successfully"}


@router.get("/sources/{source_id}/stats", tags=["Sources"])
async def get_source_stats(source_id: str):
    """Get source credibility statistics"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    stats = scorer.get_source_stats(source_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Source not found")

    return stats


@router.post("/sources/rank", tags=["Sources"])
async def rank_sources(source_ids: List[str]):
    """Rank sources by credibility"""
    from ..core.dependencies import get_credibility_scorer

    scorer = get_credibility_scorer()
    ranked = scorer.rank_sources(source_ids)

    return {
        "total_sources": len(ranked),
        "sources": ranked
    }


# Health Check
@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }


@router.get("/info", tags=["System"])
async def get_api_info():
    """API info endpoint"""
    from ..core.config import settings
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Multi-Source OSINT Intelligence Platform",
        "docs_url": "/docs",
        "api_base": "/api/v1"
    }
