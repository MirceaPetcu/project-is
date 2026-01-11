import { useState, useEffect } from 'react';
import {
  Database,
  Plus,
  Loader,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import CredibilityBadge from '../components/CredibilityBadge';
import { registerSource, getSources } from '../api/client';
import type { Source, SourceType } from '../types';

const sourceTypes: { value: SourceType; label: string }[] = [
  { value: 'news', label: 'News' },
  { value: 'social_media', label: 'Social Media' },
  { value: 'public_records', label: 'Public Records' },
  { value: 'forum', label: 'Forum' },
  { value: 'blog', label: 'Blog' },
  { value: 'academic', label: 'Academic' },
  { value: 'government', label: 'Government' },
  { value: 'other', label: 'Other' },
];

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceName, setSourceName] = useState('');
  const [sourceType, setSourceType] = useState<SourceType>('news');
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setFetchingData(true);
      const response = await getSources();
      setSources(response.sources);
    } catch (err) {
      console.error('Failed to fetch sources:', err);
    } finally {
      setFetchingData(false);
    }
  };

  const handleRegisterSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceUrl.trim() || !sourceName.trim()) return;

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const newSource = await registerSource({
        name: sourceName,
        type: sourceType,
        url: sourceUrl,
        credibility_score: 0.5,
        credibility_level: 'unverified',
        metadata: {},
      });
      setSources((prev) => [...prev, newSource]);
      setSuccess(true);
      setSourceName('');
      setSourceUrl('');
      setSourceType('news');
      setTimeout(() => {
        setShowAddModal(false);
        setSuccess(false);
      }, 1500);
    } catch (err) {
      setError('Failed to register source. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowAddModal(false);
    setError(null);
    setSuccess(false);
    setSourceName('');
    setSourceUrl('');
    setSourceType('news');
  };

  return (
    <>
      <header className="content-header">
        <div className="flex justify-between items-center">
          <div>
            <h1>Sources</h1>
            <p>Manage data sources and ingestion</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus size={16} />
            Add Source
          </button>
        </div>
      </header>

      <div className="content-body">
        {/* Stats */}
        <div className="grid grid-4 mb-6">
          <div className="stat-card">
            <span className="stat-label">Total Sources</span>
            <div className="stat-value">{sources.length}</div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Documents</span>
            <div className="stat-value">-</div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Verified Sources</span>
            <div className="stat-value">
              {sources.filter((s) => s.credibility_level === 'verified').length}
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-label">Avg. Credibility</span>
            <div className="stat-value">
              {sources.length > 0
                ? Math.round(
                    (sources.reduce((sum, s) => sum + s.credibility_score, 0) /
                      sources.length) *
                      100
                  )
                : 0}
              %
            </div>
          </div>
        </div>

        {/* Sources table */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title flex items-center gap-2">
              <Database size={16} />
              Active Sources
            </h3>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {fetchingData ? (
              <div className="flex items-center justify-center" style={{ padding: '2rem' }}>
                <Loader className="spinner" size={24} />
              </div>
            ) : sources.length === 0 ? (
              <div className="text-center text-muted" style={{ padding: '2rem' }}>
                No sources registered yet. Click "Add Source" to get started.
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Type</th>
                    <th>Credibility</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source) => (
                    <tr key={source.id}>
                      <td>
                        <div>
                          <div style={{ fontWeight: 500 }}>{source.name}</div>
                          <div className="text-sm text-muted">{source.url}</div>
                        </div>
                      </td>
                      <td style={{ textTransform: 'capitalize' }}>
                        {source.type.replace('_', ' ')}
                      </td>
                      <td>
                        <CredibilityBadge score={source.credibility_score} />
                      </td>
                      <td>
                        <span className="badge badge-success">Active</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Add Source Modal */}
        {showAddModal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={closeModal}
          >
            <div
              className="card"
              style={{ width: '500px', maxHeight: '80vh', overflow: 'auto' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="card-header">
                <h3 className="card-title">Add New Source</h3>
                <button className="btn btn-ghost btn-sm" onClick={closeModal}>
                  ×
                </button>
              </div>
              <div className="card-body">
                <form onSubmit={handleRegisterSource}>
                  <div className="input-group mb-4">
                    <label className="input-label">Source Name</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Reuters News"
                      value={sourceName}
                      onChange={(e) => setSourceName(e.target.value)}
                    />
                  </div>

                  <div className="input-group mb-4">
                    <label className="input-label">Source Type</label>
                    <select
                      className="input"
                      value={sourceType}
                      onChange={(e) => setSourceType(e.target.value as SourceType)}
                    >
                      {sourceTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="input-group mb-4">
                    <label className="input-label">Source URL</label>
                    <input
                      type="url"
                      className="input"
                      placeholder="https://example.com"
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                    />
                  </div>

                  {error && (
                    <div className="alert alert-danger mb-4">
                      <XCircle className="alert-icon" />
                      <div className="alert-content">{error}</div>
                    </div>
                  )}

                  {success && (
                    <div className="alert alert-success mb-4">
                      <CheckCircle className="alert-icon" />
                      <div className="alert-content">
                        <div className="alert-title">Source Registered</div>
                        <p>The source has been successfully added.</p>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 justify-end">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={closeModal}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading || !sourceUrl.trim() || !sourceName.trim()}
                    >
                      {loading ? (
                        <Loader className="spinner" size={16} />
                      ) : (
                        <Plus size={16} />
                      )}
                      {loading ? 'Adding...' : 'Add Source'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}