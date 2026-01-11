// Source types
export type SourceType =
  | 'news'
  | 'social_media'
  | 'public_records'
  | 'forum'
  | 'blog'
  | 'academic'
  | 'government'
  | 'other';

export type CredibilityLevel =
  | 'verified'
  | 'high'
  | 'medium'
  | 'low'
  | 'unverified'
  | 'disputed';

export type QueryMode = 'naive' | 'local' | 'global' | 'hybrid';

// Core models
export interface Source {
  id?: string;
  name: string;
  type: SourceType;
  url?: string;
  credibility_score: number;
  credibility_level: CredibilityLevel;
  metadata?: Record<string, unknown>;
  first_seen?: string;
  last_updated?: string;
}

export interface Entity {
  id?: string;
  name: string;
  entity_type: string;
  aliases: string[];
  attributes: Record<string, unknown>;
  confidence: number;
  sources: string[];
  first_mentioned?: string;
  last_mentioned?: string;
  location?: { lat: number; lon: number };
}

export interface Document {
  id?: string;
  source_id: string;
  title: string;
  content: string;
  url?: string;
  author?: string;
  published_date?: string;
  collected_date?: string;
  language: string;
  entities_mentioned: string[];
  location?: { lat: number; lon: number };
  metadata?: Record<string, unknown>;
}

export interface Relationship {
  id?: string;
  source_entity: string;
  target_entity: string;
  relationship_type: string;
  weight: number;
  credibility_weighted_score: number;
  sources: string[];
  attributes: Record<string, unknown>;
  first_observed?: string;
  last_observed?: string;
}

// Request/Response types
export interface QueryRequest {
  query: string;
  mode?: QueryMode;
  top_k?: number;
  only_credible_sources?: boolean;
  min_credibility?: number;
  time_range_days?: number;
  entity_filter?: string[];
  source_type_filter?: SourceType[];
}

export interface QueryResponse {
  query: string;
  answer: string;
  sources: Source[];
  entities: Entity[];
  confidence: number;
  execution_time: number;
}

export interface IngestRequest {
  source: Source;
  documents: Document[];
  extract_entities?: boolean;
  detect_misinformation?: boolean;
}

export interface IngestResponse {
  source_id: string;
  documents_processed: number;
  entities_extracted: number;
  misinformation_alerts: MisinformationAlert[];
  errors: string[];
}

export interface MisinformationAlert {
  id?: string;
  document_id: string;
  claim: string;
  contradiction_score: number;
  contradicting_sources: string[];
  evidence: string[];
  detected_at: string;
}

export interface NarrativePattern {
  id?: string;
  narrative_theme: string;
  entities_involved: string[];
  sources: string[];
  coordination_score: number;
  temporal_pattern: Record<string, number>;
  first_detected?: string;
  last_updated?: string;
}

export interface PredictiveAlert {
  id?: string;
  alert_type: string;
  entities: string[];
  description: string;
  confidence: number;
  supporting_evidence: string[];
  created_at: string;
}

export interface TimelineEvent {
  timestamp: string;
  description: string;
  sources: string[];
  confidence: number;
}

export interface GeoCluster {
  id?: string;
  center_location: { lat: number; lon: number };
  radius_km: number;
  entities: string[];
  entity_count: number;
  average_credibility: number;
  temporal_activity: Record<string, number>;
}

export interface SourceStats {
  source_id: string;
  current_score: number;
  documents_published: number;
  verified_accurate: number;
  verified_inaccurate: number;
  accuracy_rate: number;
  last_updated: string;
}

export interface EntityNetwork {
  entity: Entity;
  related_entities: Array<{
    entity: Entity;
    relationship: Relationship;
  }>;
  depth: number;
}

export interface VerificationResult {
  claim: string;
  verification_score: number;
  supporting_sources: Source[];
  contradicting_sources: Source[];
  confidence: number;
}

export interface HealthCheck {
  status: string;
  timestamp: string;
}
