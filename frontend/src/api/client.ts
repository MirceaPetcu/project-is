import type {
  QueryRequest,
  QueryResponse,
  Entity,
  EntityNetwork,
  Source,
  SourceStats,
  PredictiveAlert,
  NarrativePattern,
  VerificationResult,
  TimelineEvent,
  GeoCluster,
  IngestRequest,
  IngestResponse,
  HealthCheck,
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Query endpoints
export async function query(request: QueryRequest): Promise<QueryResponse> {
  return fetchJson<QueryResponse>(`${API_BASE}/query`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Entity endpoints
export async function getEntities(
  limit = 50,
  entityType?: string
): Promise<{ total: number; entities: Entity[] }> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (entityType) params.append('entity_type', entityType);
  return fetchJson(`${API_BASE}/entities?${params}`);
}

export async function getEntity(entityId: string): Promise<Entity> {
  return fetchJson(`${API_BASE}/entities/${entityId}`);
}

export async function getEntityNetwork(
  entityId: string,
  depth = 1
): Promise<EntityNetwork> {
  return fetchJson(`${API_BASE}/entities/${entityId}/network?depth=${depth}`);
}

// Analysis endpoints
export async function detectNarratives(
  entityIds: string[],
  timeWindowDays?: number
): Promise<{ narratives_detected: number; narratives: NarrativePattern[] }> {
  const params = new URLSearchParams();
  entityIds.forEach((id) => params.append('entity_ids', id));
  if (timeWindowDays) params.append('time_window_days', timeWindowDays.toString());
  return fetchJson(`${API_BASE}/analysis/narratives?${params}`, { method: 'POST' });
}

export async function getNarrativeSummary(): Promise<{
  summary: string;
  total_narratives: number;
  patterns: NarrativePattern[];
}> {
  return fetchJson(`${API_BASE}/analysis/narratives/summary`);
}

export async function analyzeGaps(entityId: string): Promise<{
  entity: string;
  known_info_summary: string;
  gap_analysis: string;
  collection_priorities: string[];
}> {
  return fetchJson(`${API_BASE}/analysis/gaps/${entityId}`);
}

export async function verifyClaim(
  claim: string,
  minSources = 3
): Promise<VerificationResult> {
  const params = new URLSearchParams({
    claim,
    min_sources: minSources.toString(),
  });
  return fetchJson(`${API_BASE}/analysis/verify?${params}`, { method: 'POST' });
}

export async function getAlerts(
  limit = 20
): Promise<{ total_alerts: number; alerts: PredictiveAlert[] }> {
  return fetchJson(`${API_BASE}/analysis/alerts?limit=${limit}`);
}

export async function generateAlerts(
  entityIds?: string[]
): Promise<{ alerts_generated: number; alerts: PredictiveAlert[] }> {
  const params = new URLSearchParams();
  entityIds?.forEach((id) => params.append('entity_ids', id));
  return fetchJson(`${API_BASE}/analysis/alerts/generate?${params}`, {
    method: 'POST',
  });
}

// Temporal endpoints
export async function getTimeline(
  entityId: string,
  startDate?: string,
  endDate?: string
): Promise<{ entity_id: string; event_count: number; timeline: TimelineEvent[] }> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  const queryStr = params.toString() ? `?${params}` : '';
  return fetchJson(`${API_BASE}/temporal/timeline/${entityId}${queryStr}`);
}

export async function getTemporalClusters(entityId: string): Promise<{
  entity_id: string;
  cluster_count: number;
  clusters: Array<{ start: string; end: string; event_count: number }>;
}> {
  return fetchJson(`${API_BASE}/temporal/clusters/${entityId}`);
}

export async function getTemporalAnomalies(entityId: string): Promise<{
  entity_id: string;
  anomaly_count: number;
  anomalies: Array<{ timestamp: string; description: string; severity: number }>;
}> {
  return fetchJson(`${API_BASE}/temporal/anomalies/${entityId}`);
}

export async function findConcurrentEvents(
  entityIds: string[],
  timeWindowHours = 24
): Promise<{
  concurrent_groups: number;
  groups: Array<{ entities: string[]; events: TimelineEvent[] }>;
}> {
  const params = new URLSearchParams({
    time_window_hours: timeWindowHours.toString(),
  });
  entityIds.forEach((id) => params.append('entity_ids', id));
  return fetchJson(`${API_BASE}/temporal/concurrent?${params}`, { method: 'POST' });
}

// Geographic endpoints
export async function getGeographicClusters(
  entityIds: string[],
  radiusKm?: number
): Promise<{ cluster_count: number; clusters: GeoCluster[] }> {
  const params = new URLSearchParams();
  entityIds.forEach((id) => params.append('entity_ids', id));
  if (radiusKm) params.append('radius_km', radiusKm.toString());
  return fetchJson(`${API_BASE}/geographic/clusters?${params}`, { method: 'POST' });
}

export async function getEntityMovement(entityId: string): Promise<{
  entity_id: string;
  locations: Array<{ lat: number; lon: number; timestamp: string }>;
  movement_pattern: string;
}> {
  return fetchJson(`${API_BASE}/geographic/movement/${entityId}`);
}

export async function findNearbyEntities(
  latitude: number,
  longitude: number,
  radiusKm: number,
  entityIds?: string[]
): Promise<{
  location: { lat: number; lon: number };
  radius_km: number;
  entities_found: number;
  entities: Entity[];
}> {
  const params = new URLSearchParams({
    latitude: latitude.toString(),
    longitude: longitude.toString(),
    radius_km: radiusKm.toString(),
  });
  entityIds?.forEach((id) => params.append('entity_ids', id));
  return fetchJson(`${API_BASE}/geographic/nearby?${params}`, { method: 'POST' });
}

export async function getGeographicHotspots(
  entityIds: string[],
  gridSizeKm = 50
): Promise<{
  hotspot_count: number;
  hotspots: Array<{ location: { lat: number; lon: number }; intensity: number }>;
}> {
  const params = new URLSearchParams({ grid_size_km: gridSizeKm.toString() });
  entityIds.forEach((id) => params.append('entity_ids', id));
  return fetchJson(`${API_BASE}/geographic/hotspots?${params}`, { method: 'POST' });
}

// Source endpoints
export async function registerSource(source: Omit<Source, 'id'>): Promise<Source> {
  return fetchJson(`${API_BASE}/sources`, {
    method: 'POST',
    body: JSON.stringify(source),
  });
}

export async function getSources(): Promise<{ total: number; sources: Source[] }> {
  return fetchJson(`${API_BASE}/sources`);
}

export async function getSource(sourceId: string): Promise<Source> {
  return fetchJson(`${API_BASE}/sources/${sourceId}`);
}

export async function deleteSource(sourceId: string): Promise<{ message: string }> {
  return fetchJson(`${API_BASE}/sources/${sourceId}`, { method: 'DELETE' });
}

export async function getSourceStats(sourceId: string): Promise<SourceStats> {
  return fetchJson(`${API_BASE}/sources/${sourceId}/stats`);
}

export async function rankSources(
  sourceIds: string[]
): Promise<{ total_sources: number; sources: Array<Source & { rank: number }> }> {
  const params = new URLSearchParams();
  sourceIds.forEach((id) => params.append('source_ids', id));
  return fetchJson(`${API_BASE}/sources/rank?${params}`, { method: 'POST' });
}

// Ingestion endpoints
export async function ingestBatch(request: IngestRequest): Promise<IngestResponse> {
  return fetchJson(`${API_BASE}/ingest/batch`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function ingestFromRss(
  source: Source,
  feedUrl: string,
  maxItems = 50
): Promise<IngestResponse> {
  const params = new URLSearchParams({
    feed_url: feedUrl,
    max_items: maxItems.toString(),
  });
  return fetchJson(`${API_BASE}/ingest/rss?${params}`, {
    method: 'POST',
    body: JSON.stringify(source),
  });
}

export async function ingestFromWeb(
  source: Source,
  url: string
): Promise<IngestResponse> {
  return fetchJson(`${API_BASE}/ingest/web?url=${encodeURIComponent(url)}`, {
    method: 'POST',
    body: JSON.stringify(source),
  });
}

// Health endpoint
export async function healthCheck(): Promise<HealthCheck> {
  return fetchJson('/health');
}

// Root endpoint
export async function getApiInfo(): Promise<{
  name: string;
  version: string;
  description: string;
  docs_url: string;
  api_base: string;
}> {
  return fetchJson('/api/v1/info');
}
