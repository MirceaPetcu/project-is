import { useState } from 'react';
import {
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader,
} from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import CredibilityBadge from '../components/CredibilityBadge';
import { verifyClaim, detectNarratives, analyzeGaps } from '../api/client';
import type { VerificationResult, NarrativePattern } from '../types';

type Tab = 'verify' | 'narratives' | 'gaps';

export default function Analysis() {
  const [activeTab, setActiveTab] = useState<Tab>('verify');

  return (
    <>
      <header className="content-header">
        <h1>Analysis</h1>
        <p>Verify claims, detect narratives, and identify intelligence gaps</p>
      </header>

      <div className="content-body">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'verify' ? 'active' : ''}`}
            onClick={() => setActiveTab('verify')}
          >
            <Shield size={16} style={{ marginRight: '8px' }} />
            Claim Verification
          </button>
          <button
            className={`tab ${activeTab === 'narratives' ? 'active' : ''}`}
            onClick={() => setActiveTab('narratives')}
          >
            <TrendingUp size={16} style={{ marginRight: '8px' }} />
            Narrative Detection
          </button>
          <button
            className={`tab ${activeTab === 'gaps' ? 'active' : ''}`}
            onClick={() => setActiveTab('gaps')}
          >
            <AlertTriangle size={16} style={{ marginRight: '8px' }} />
            Gap Analysis
          </button>
        </div>

        {activeTab === 'verify' && <ClaimVerification />}
        {activeTab === 'narratives' && <NarrativeDetection />}
        {activeTab === 'gaps' && <GapAnalysis />}
      </div>
    </>
  );
}

function ClaimVerification() {
  const [claim, setClaim] = useState('');
  const [minSources, setMinSources] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await verifyClaim(claim, minSources);
      setResult(response);
    } catch (err) {
      setError('Failed to verify claim. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card mb-6">
        <div className="card-body">
          <form onSubmit={handleVerify}>
            <div className="input-group mb-4">
              <label className="input-label">Claim to Verify</label>
              <textarea
                className="input"
                rows={3}
                placeholder="Enter a claim to verify against the knowledge base..."
                value={claim}
                onChange={(e) => setClaim(e.target.value)}
                style={{ resize: 'vertical' }}
              />
            </div>

            <div className="flex items-center gap-4">
              <div className="input-group" style={{ width: '200px' }}>
                <label className="input-label">Minimum Sources</label>
                <select
                  className="input"
                  value={minSources}
                  onChange={(e) => setMinSources(parseInt(e.target.value))}
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n} source{n > 1 ? 's' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !claim.trim()}
                style={{ marginTop: '24px' }}
              >
                {loading ? <Loader className="spinner" size={16} /> : <Shield size={16} />}
                Verify Claim
              </button>
            </div>
          </form>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mb-4">
          <XCircle className="alert-icon" />
          <div className="alert-content">{error}</div>
        </div>
      )}

      {result && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Verification Result</h3>
            <span
              className={`badge ${
                result.verification_score >= 0.7
                  ? 'badge-success'
                  : result.verification_score >= 0.4
                  ? 'badge-warning'
                  : 'badge-danger'
              }`}
            >
              {result.verification_score >= 0.7
                ? 'Likely True'
                : result.verification_score >= 0.4
                ? 'Uncertain'
                : 'Likely False'}
            </span>
          </div>
          <div className="card-body">
            <div className="mb-4">
              <label className="text-sm text-muted">Claim</label>
              <p className="mt-1">{result.claim}</p>
            </div>

            <div className="grid grid-2 mb-4">
              <div>
                <label className="text-sm text-muted">Verification Score</label>
                <div className="flex items-center gap-2 mt-1">
                  <div className="progress" style={{ flex: 1 }}>
                    <div
                      className={`progress-bar ${
                        result.verification_score >= 0.7
                          ? 'success'
                          : result.verification_score >= 0.4
                          ? 'warning'
                          : 'danger'
                      }`}
                      style={{ width: `${result.verification_score * 100}%` }}
                    />
                  </div>
                  <span>{Math.round(result.verification_score * 100)}%</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-muted">Confidence</label>
                <div className="flex items-center gap-2 mt-1">
                  <div className="progress" style={{ flex: 1 }}>
                    <div
                      className="progress-bar"
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                  <span>{Math.round(result.confidence * 100)}%</span>
                </div>
              </div>
            </div>

            <div className="grid grid-2">
              <div>
                <label className="text-sm text-muted flex items-center gap-2">
                  <CheckCircle size={14} style={{ color: 'var(--accent-success)' }} />
                  Supporting Sources ({result.supporting_sources.length})
                </label>
                <div className="mt-2">
                  {result.supporting_sources.map((source, i) => (
                    <div key={i} className="flex items-center gap-2 mb-2">
                      <span>{source.name}</span>
                      <CredibilityBadge score={source.credibility_score} />
                    </div>
                  ))}
                  {result.supporting_sources.length === 0 && (
                    <p className="text-muted text-sm">No supporting sources found</p>
                  )}
                </div>
              </div>
              <div>
                <label className="text-sm text-muted flex items-center gap-2">
                  <XCircle size={14} style={{ color: 'var(--accent-danger)' }} />
                  Contradicting Sources ({result.contradicting_sources.length})
                </label>
                <div className="mt-2">
                  {result.contradicting_sources.map((source, i) => (
                    <div key={i} className="flex items-center gap-2 mb-2">
                      <span>{source.name}</span>
                      <CredibilityBadge score={source.credibility_score} />
                    </div>
                  ))}
                  {result.contradicting_sources.length === 0 && (
                    <p className="text-muted text-sm">No contradicting sources found</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function NarrativeDetection() {
  const [entityIds, setEntityIds] = useState('');
  const [timeWindow, setTimeWindow] = useState(7);
  const [loading, setLoading] = useState(false);
  const [narratives, setNarratives] = useState<NarrativePattern[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleDetect = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);
    setError(null);

    try {
      const ids = entityIds.split(',').map((id) => id.trim()).filter(Boolean);
      const response = await detectNarratives(ids, timeWindow);
      setNarratives(response.narratives);
    } catch (err) {
      setError('Failed to detect narratives. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card mb-6">
        <div className="card-body">
          <form onSubmit={handleDetect}>
            <div className="flex gap-4">
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">Entity IDs (comma-separated)</label>
                <input
                  type="text"
                  className="input"
                  placeholder="entity1, entity2, entity3..."
                  value={entityIds}
                  onChange={(e) => setEntityIds(e.target.value)}
                />
              </div>

              <div className="input-group" style={{ width: '160px' }}>
                <label className="input-label">Time Window</label>
                <select
                  className="input"
                  value={timeWindow}
                  onChange={(e) => setTimeWindow(parseInt(e.target.value))}
                >
                  <option value={1}>1 day</option>
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                </select>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ marginTop: '24px' }}
              >
                {loading ? <Loader className="spinner" size={16} /> : <TrendingUp size={16} />}
                Detect Narratives
              </button>
            </div>
          </form>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mb-4">
          <XCircle className="alert-icon" />
          <div className="alert-content">{error}</div>
        </div>
      )}

      {loading && <LoadingSpinner />}

      {narratives.length > 0 && (
        <div className="grid grid-2">
          {narratives.map((narrative, i) => (
            <div key={i} className="card">
              <div className="card-header">
                <h3 className="card-title">{narrative.narrative_theme}</h3>
                <span className="badge badge-primary">
                  {Math.round(narrative.coordination_score * 100)}% coordination
                </span>
              </div>
              <div className="card-body">
                <div className="mb-4">
                  <label className="text-sm text-muted">Entities Involved</label>
                  <div className="flex gap-2 flex-wrap mt-1">
                    {narrative.entities_involved.map((entity, j) => (
                      <span key={j} className="badge badge-neutral">
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted">Sources</label>
                  <p className="mt-1">{narrative.sources.length} sources</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GapAnalysis() {
  const [entityId, setEntityId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    entity: string;
    known_info_summary: string;
    gap_analysis: string;
    collection_priorities: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!entityId.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await analyzeGaps(entityId);
      setResult(response);
    } catch (err) {
      setError('Failed to analyze gaps. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card mb-6">
        <div className="card-body">
          <form onSubmit={handleAnalyze}>
            <div className="flex gap-4">
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">Entity ID</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Enter entity ID to analyze..."
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
                {loading ? (
                  <Loader className="spinner" size={16} />
                ) : (
                  <AlertTriangle size={16} />
                )}
                Analyze Gaps
              </button>
            </div>
          </form>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mb-4">
          <XCircle className="alert-icon" />
          <div className="alert-content">{error}</div>
        </div>
      )}

      {loading && <LoadingSpinner />}

      {result && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Gap Analysis: {result.entity}</h3>
          </div>
          <div className="card-body">
            <div className="mb-4">
              <label className="text-sm text-muted">Known Information</label>
              <p className="mt-2">{result.known_info_summary}</p>
            </div>

            <div className="mb-4">
              <label className="text-sm text-muted">Gap Analysis</label>
              <p className="mt-2">{result.gap_analysis}</p>
            </div>

            <div>
              <label className="text-sm text-muted">Collection Priorities</label>
              <ul className="mt-2" style={{ paddingLeft: '20px' }}>
                {result.collection_priorities.map((priority, i) => (
                  <li key={i} className="mb-2">
                    {priority}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
