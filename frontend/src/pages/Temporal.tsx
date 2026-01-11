import { useState } from 'react';
import { Clock, TrendingUp, AlertCircle, Loader } from 'lucide-react';
import { format } from 'date-fns';
import LoadingSpinner from '../components/LoadingSpinner';
import { getTimeline, getTemporalClusters, getTemporalAnomalies } from '../api/client';
import type { TimelineEvent } from '../types';

export default function Temporal() {
  const [entityId, setEntityId] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [clusters, setClusters] = useState<
    Array<{ start: string; end: string; event_count: number }>
  >([]);
  const [anomalies, setAnomalies] = useState<
    Array<{ timestamp: string; description: string; severity: number }>
  >([]);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!entityId.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const [timelineRes, clustersRes, anomaliesRes] = await Promise.allSettled([
        getTimeline(entityId),
        getTemporalClusters(entityId),
        getTemporalAnomalies(entityId),
      ]);

      if (timelineRes.status === 'fulfilled') {
        setTimeline(timelineRes.value.timeline);
      }
      if (clustersRes.status === 'fulfilled') {
        setClusters(clustersRes.value.clusters);
      }
      if (anomaliesRes.status === 'fulfilled') {
        setAnomalies(anomaliesRes.value.anomalies);
      }
    } catch (err) {
      setError('Failed to fetch temporal data. Make sure the backend is running.');
      console.error(err);
      // Demo data
      setTimeline([
        {
          timestamp: '2024-03-15T14:30:00Z',
          description: 'Initial mention in news article',
          sources: ['source1'],
          confidence: 0.9,
        },
        {
          timestamp: '2024-03-16T09:00:00Z',
          description: 'Social media discussion spike',
          sources: ['source2', 'source3'],
          confidence: 0.85,
        },
        {
          timestamp: '2024-03-17T16:45:00Z',
          description: 'Official statement released',
          sources: ['source1'],
          confidence: 0.95,
        },
        {
          timestamp: '2024-03-18T11:20:00Z',
          description: 'Analysis report published',
          sources: ['source4'],
          confidence: 0.8,
        },
      ]);
      setClusters([
        { start: '2024-03-15T00:00:00Z', end: '2024-03-17T00:00:00Z', event_count: 12 },
        { start: '2024-03-20T00:00:00Z', end: '2024-03-22T00:00:00Z', event_count: 8 },
      ]);
      setAnomalies([
        {
          timestamp: '2024-03-16T09:00:00Z',
          description: 'Unusual activity spike detected',
          severity: 0.8,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="content-header">
        <h1>Temporal Analysis</h1>
        <p>Explore event timelines and temporal patterns</p>
      </header>

      <div className="content-body">
        <div className="card mb-6">
          <div className="card-body">
            <form onSubmit={handleAnalyze}>
              <div className="flex gap-4">
                <div className="input-group" style={{ flex: 1 }}>
                  <label className="input-label">Entity ID</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Enter entity ID to analyze temporal patterns..."
                    value={entityId}
                    onChange={(e) => setEntityId(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !entityId.trim()}
                  style={{ marginTop: '24px' }}
                >
                  {loading ? <Loader className="spinner" size={16} /> : <Clock size={16} />}
                  Analyze Timeline
                </button>
              </div>
            </form>
          </div>
        </div>

        {error && (
          <div className="alert alert-warning mb-4">
            <AlertCircle className="alert-icon" />
            <div className="alert-content">{error} Showing demo data.</div>
          </div>
        )}

        {loading && <LoadingSpinner />}

        {(timeline.length > 0 || clusters.length > 0 || anomalies.length > 0) && (
          <div className="grid grid-3">
            {/* Timeline */}
            <div className="card" style={{ gridColumn: 'span 2' }}>
              <div className="card-header">
                <h3 className="card-title flex items-center gap-2">
                  <Clock size={16} />
                  Event Timeline
                </h3>
                <span className="badge badge-neutral">{timeline.length} events</span>
              </div>
              <div className="card-body">
                {timeline.length > 0 ? (
                  <div className="timeline">
                    {timeline.map((event, i) => (
                      <div key={i} className="timeline-item">
                        <div className="timeline-dot" />
                        <div className="timeline-date">
                          {format(new Date(event.timestamp), 'MMM d, yyyy HH:mm')}
                        </div>
                        <div className="timeline-content">
                          <p>{event.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-muted">
                            <span>{event.sources.length} sources</span>
                            <span>Confidence: {Math.round(event.confidence * 100)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No timeline events found</p>
                )}
              </div>
            </div>

            {/* Sidebar with clusters and anomalies */}
            <div className="flex flex-col gap-6">
              {/* Temporal Clusters */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title flex items-center gap-2">
                    <TrendingUp size={16} />
                    Activity Clusters
                  </h3>
                </div>
                <div className="card-body">
                  {clusters.length > 0 ? (
                    <div className="flex flex-col gap-4">
                      {clusters.map((cluster, i) => (
                        <div
                          key={i}
                          style={{
                            padding: '12px',
                            background: 'var(--bg-tertiary)',
                            borderRadius: 'var(--radius-md)',
                          }}
                        >
                          <div className="flex justify-between items-center">
                            <span className="text-sm">
                              {format(new Date(cluster.start), 'MMM d')} -{' '}
                              {format(new Date(cluster.end), 'MMM d')}
                            </span>
                            <span className="badge badge-primary">
                              {cluster.event_count} events
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted text-sm">No clusters detected</p>
                  )}
                </div>
              </div>

              {/* Anomalies */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title flex items-center gap-2">
                    <AlertCircle size={16} />
                    Anomalies
                  </h3>
                </div>
                <div className="card-body">
                  {anomalies.length > 0 ? (
                    <div className="flex flex-col gap-4">
                      {anomalies.map((anomaly, i) => (
                        <div
                          key={i}
                          className={`alert ${
                            anomaly.severity >= 0.7
                              ? 'alert-danger'
                              : anomaly.severity >= 0.4
                              ? 'alert-warning'
                              : 'alert-info'
                          }`}
                          style={{ padding: '12px' }}
                        >
                          <div>
                            <div className="text-sm font-medium">{anomaly.description}</div>
                            <div className="text-xs mt-1" style={{ opacity: 0.8 }}>
                              {format(new Date(anomaly.timestamp), 'MMM d, yyyy HH:mm')}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted text-sm">No anomalies detected</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
