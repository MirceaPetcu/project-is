from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Source types for OSINT data"""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    PUBLIC_RECORDS = "public_records"
    FORUM = "forum"
    BLOG = "blog"
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    OTHER = "other"


class CredibilityLevel(str, Enum):
    """Source credibility levels"""
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class QueryMode(str, Enum):
    """Query modes for RAG"""
    NAIVE = "naive"
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"


class Source(BaseModel):
    """Data source model"""
    id: Optional[str] = None
    name: str
    type: SourceType
    url: Optional[HttpUrl] = None
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    credibility_level: CredibilityLevel = CredibilityLevel.MEDIUM
    metadata: Dict[str, Any] = {}
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    """Entity extracted from sources"""
    id: Optional[str] = None
    name: str
    entity_type: str  # person, organization, location, event, etc.
    aliases: List[str] = []
    attributes: Dict[str, Any] = {}
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sources: List[str] = []  # List of source IDs
    first_mentioned: datetime = Field(default_factory=datetime.utcnow)
    last_mentioned: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[Dict[str, float]] = None  # lat, lon


class Relationship(BaseModel):
    """Relationship between entities"""
    id: Optional[str] = None
    source_entity: str
    target_entity: str
    relationship_type: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    credibility_weighted_score: float = Field(default=0.5, ge=0.0, le=1.0)
    sources: List[str] = []
    attributes: Dict[str, Any] = {}
    first_observed: datetime = Field(default_factory=datetime.utcnow)
    last_observed: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Document/content from a source"""
    id: Optional[str] = None
    source_id: str
    title: str
    content: str
    url: Optional[HttpUrl] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    collected_date: datetime = Field(default_factory=datetime.utcnow)
    language: str = "en"
    entities_mentioned: List[str] = []
    location: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = {}


class IngestRequest(BaseModel):
    """Request to ingest data"""
    source: Source
    documents: List[Document]
    extract_entities: bool = True
    detect_misinformation: bool = True


class QueryRequest(BaseModel):
    """Query request"""
    query: str
    mode: QueryMode = QueryMode.HYBRID
    top_k: int = Field(default=10, ge=1, le=100)
    only_credible_sources: bool = True
    min_credibility: float = Field(default=0.3, ge=0.0, le=1.0)
    time_range_days: Optional[int] = None
    entity_filter: Optional[List[str]] = None
    source_type_filter: Optional[List[SourceType]] = None


class QueryResponse(BaseModel):
    """Query response"""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    entities: List[Entity]
    confidence: float
    execution_time: float


class MisinformationAlert(BaseModel):
    """Misinformation detection alert"""
    id: Optional[str] = None
    document_id: str
    claim: str
    contradiction_score: float
    contradicting_sources: List[str]
    evidence: List[str]
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class NarrativePattern(BaseModel):
    """Detected narrative pattern"""
    id: Optional[str] = None
    narrative_theme: str
    entities_involved: List[str]
    sources: List[str]
    coordination_score: float
    temporal_pattern: Dict[str, int]  # timestamp -> mention count
    first_detected: datetime
    last_updated: datetime


class PredictiveAlert(BaseModel):
    """Predictive alert for emerging patterns"""
    id: Optional[str] = None
    alert_type: str
    entities: List[str]
    description: str
    confidence: float
    supporting_evidence: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeoCluster(BaseModel):
    """Geographic cluster of entities"""
    id: Optional[str] = None
    center_location: Dict[str, float]  # lat, lon
    radius_km: float
    entities: List[str]
    entity_count: int
    average_credibility: float
    temporal_activity: Dict[str, int]


class EntityResolutionResult(BaseModel):
    """Result of entity resolution"""
    canonical_entity_id: str
    merged_entities: List[str]
    confidence: float
    resolution_method: str
