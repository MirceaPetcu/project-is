import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, Loader, Bell, Filter } from 'lucide-react';
import { format } from 'date-fns';
import AlertCard from '../components/AlertCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { getAlerts, generateAlerts } from '../api/client';
import type { PredictiveAlert } from '../types';

export default function Alerts() {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [alerts, setAlerts] = useState<PredictiveAlert[]>([]);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchAlerts();
  }, []);

  async function fetchAlerts() {
    setLoading(true);
    try {
      const response = await getAlerts(50);
      setAlerts(response.alerts);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      // Demo data
      setAlerts([
        {
          id: '1',
          alert_type: 'Emerging Pattern',
          entities: ['entity1', 'entity2'],
          description:
            'Unusual correlation detected between multiple entities across different source types. Activity levels have increased 300% in the past 24 hours.',
          confidence: 0.89,
          supporting_evidence: ['evidence1', 'evidence2'],
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          alert_type: 'Narrative Shift',
          entities: ['entity3'],
          description:
            'New narrative theme emerging across social media platforms. Coordination score suggests potential organized campaign.',
          confidence: 0.76,
          supporting_evidence: ['evidence3'],
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '3',
          alert_type: 'Misinformation',
          entities: ['entity4', 'entity5'],
          description:
            'Contradictory claims detected from low-credibility sources. Cross-reference with verified sources shows significant discrepancy.',
          confidence: 0.92,
          supporting_evidence: ['evidence4', 'evidence5'],
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
        {
          id: '4',
          alert_type: 'Geographic Cluster',
          entities: ['entity6'],
          description:
            'New geographic activity hotspot detected in previously quiet region. Multiple entities now showing presence.',
          confidence: 0.68,
          supporting_evidence: ['evidence6'],
          created_at: new Date(Date.now() - 10800000).toISOString(),
        },
        {
          id: '5',
          alert_type: 'Temporal Anomaly',
          entities: ['entity7', 'entity8'],
          description:
            'Unusual timing pattern detected. Activity spike outside normal operating hours suggests automated or coordinated behavior.',
          confidence: 0.81,
          supporting_evidence: ['evidence7'],
          created_at: new Date(Date.now() - 14400000).toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateAlerts() {
    setGenerating(true);
    try {
      const response = await generateAlerts();
      if (response.alerts.length > 0) {
        setAlerts((prev) => [...response.alerts, ...prev]);
      }
    } catch (err) {
      console.error('Failed to generate alerts:', err);
    } finally {
      setGenerating(false);
    }
  }

  const alertTypes = ['all', ...new Set(alerts.map((a) => a.alert_type))];
  const filteredAlerts =
    filter === 'all' ? alerts : alerts.filter((a) => a.alert_type === filter);

  const criticalCount = alerts.filter((a) => a.confidence >= 0.8).length;
  const warningCount = alerts.filter(
    (a) => a.confidence >= 0.5 && a.confidence < 0.8
  ).length;

  return (
    <>
      <header className="content-header">
        <div className="flex justify-between items-center">
          <div>
            <h1>Alerts</h1>
            <p>Predictive alerts and pattern detection</p>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-secondary" onClick={fetchAlerts} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spinner' : ''} />
              Refresh
            </button>
            <button
              className="btn btn-primary"
              onClick={handleGenerateAlerts}
              disabled={generating}
            >
              {generating ? (
                <Loader className="spinner" size={16} />
              ) : (
                <Bell size={16} />
              )}
              Generate New
            </button>
          </div>
        </div>
      </header>

      <div className="content-body">
        {/* Stats */}
        <div className="grid grid-4 mb-6">
          <div className="stat-card">
            <span className="stat-label">Total Alerts</span>
            <div className="stat-value">{alerts.length}</div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Critical</span>
            <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>
              {criticalCount}
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Warning</span>
            <div className="stat-value" style={{ color: 'var(--accent-warning)' }}>
              {warningCount}
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Info</span>
            <div className="stat-value" style={{ color: 'var(--accent-info)' }}>
              {alerts.length - criticalCount - warningCount}
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-4 mb-6">
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <div className="flex gap-2">
            {alertTypes.map((type) => (
              <button
                key={type}
                className={`btn btn-sm ${filter === type ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilter(type)}
              >
                {type === 'all' ? 'All' : type}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : filteredAlerts.length === 0 ? (
          <EmptyState
            icon={<AlertTriangle size={64} />}
            title="No alerts found"
            description="No alerts match the current filter criteria"
          />
        ) : (
          <div className="flex flex-col gap-4">
            {filteredAlerts.map((alert) => (
              <div key={alert.id} className="card">
                <div className="card-body">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={`entity-icon ${
                          alert.confidence >= 0.8
                            ? 'bg-danger'
                            : alert.confidence >= 0.5
                            ? 'bg-warning'
                            : 'bg-info'
                        }`}
                        style={{
                          background:
                            alert.confidence >= 0.8
                              ? 'rgba(239, 68, 68, 0.2)'
                              : alert.confidence >= 0.5
                              ? 'rgba(245, 158, 11, 0.2)'
                              : 'rgba(6, 182, 212, 0.2)',
                          color:
                            alert.confidence >= 0.8
                              ? 'var(--accent-danger)'
                              : alert.confidence >= 0.5
                              ? 'var(--accent-warning)'
                              : 'var(--accent-info)',
                        }}
                      >
                        <AlertTriangle size={20} />
                      </div>
                      <div>
                        <h4 style={{ fontWeight: 600, marginBottom: '4px' }}>
                          {alert.alert_type}
                        </h4>
                        <span className="text-sm text-muted">
                          {format(new Date(alert.created_at), 'MMM d, yyyy HH:mm')}
                        </span>
                      </div>
                    </div>
                    <span
                      className={`badge ${
                        alert.confidence >= 0.8
                          ? 'badge-danger'
                          : alert.confidence >= 0.5
                          ? 'badge-warning'
                          : 'badge-primary'
                      }`}
                    >
                      {Math.round(alert.confidence * 100)}% confidence
                    </span>
                  </div>

                  <p style={{ marginBottom: '16px' }}>{alert.description}</p>

                  <div className="flex gap-6 text-sm">
                    <div>
                      <span className="text-muted">Entities: </span>
                      {alert.entities.slice(0, 3).join(', ')}
                      {alert.entities.length > 3 && ` +${alert.entities.length - 3} more`}
                    </div>
                    <div>
                      <span className="text-muted">Evidence: </span>
                      {alert.supporting_evidence.length} items
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
