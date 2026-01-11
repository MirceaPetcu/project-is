import { useState } from 'react';
import { Search, Clock, Shield, Sparkles } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import CredibilityBadge from '../components/CredibilityBadge';
import { query } from '../api/client';
import type { QueryRequest, QueryResponse, QueryMode } from '../types';

export default function Query() {
  const [queryText, setQueryText] = useState('');
  const [mode, setMode] = useState<QueryMode>('hybrid');
  const [minCredibility, setMinCredibility] = useState(0.3);
  const [onlyCredible, setOnlyCredible] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setLoading(true);
    setError(null);

    const request: QueryRequest = {
      query: queryText,
      mode,
      min_credibility: minCredibility,
      only_credible_sources: onlyCredible,
      top_k: 10,
    };

    try {
      const response = await query(request);
      setResult(response);
    } catch (err) {
      setError('Failed to execute query. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="content-header">
        <h1>Query Intelligence</h1>
        <p>Search the knowledge graph with natural language</p>
      </header>

      <div className="content-body">
        <div className="query-box">
          <form onSubmit={handleSubmit}>
            <div className="query-input-wrapper">
              <div className="search-input" style={{ flex: 1 }}>
                <Search />
                <input
                  type="text"
                  className="input input-lg"
                  placeholder="Ask anything about your intelligence data..."
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
                <Sparkles size={18} />
                Query
              </button>
            </div>

            <div className="query-options">
              <div className="query-option">
                <label>Mode:</label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value as QueryMode)}
                >
                  <option value="hybrid">Hybrid</option>
                  <option value="local">Local</option>
                  <option value="global">Global</option>
                  <option value="naive">Naive</option>
                </select>
              </div>

              <div className="query-option">
                <label>Min Credibility:</label>
                <select
                  value={minCredibility}
                  onChange={(e) => setMinCredibility(parseFloat(e.target.value))}
                >
                  <option value={0}>Any</option>
                  <option value={0.3}>30%+</option>
                  <option value={0.5}>50%+</option>
                  <option value={0.7}>70%+</option>
                </select>
              </div>

              <div className="query-option">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    checked={onlyCredible}
                    onChange={(e) => setOnlyCredible(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  Credible sources only
                </label>
              </div>
            </div>
          </form>
        </div>

        {loading && <LoadingSpinner />}

        {error && (
          <div className="alert alert-danger">
            <Shield className="alert-icon" />
            <div className="alert-content">
              <div className="alert-title">Query Failed</div>
              <p>{error}</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="result-card">
            <div className="result-answer">{result.answer}</div>

            <div className="result-meta">
              <span className="flex items-center gap-2">
                <Shield size={14} />
                Confidence: {Math.round(result.confidence * 100)}%
              </span>
              <span className="flex items-center gap-2">
                <Clock size={14} />
                {result.execution_time.toFixed(2)}s
              </span>
            </div>

            {result.sources.length > 0 && (
              <div className="result-sources">
                <h4>Sources</h4>
                <div>
                  {result.sources.map((source, i) => (
                    <span key={i} className="source-tag">
                      <span
                        className={`source-credibility ${
                          source.credibility_score >= 0.7
                            ? 'credibility-high'
                            : source.credibility_score >= 0.4
                            ? 'credibility-medium'
                            : 'credibility-low'
                        }`}
                      />
                      {source.name}
                      <CredibilityBadge score={source.credibility_score} showLabel={false} />
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.entities.length > 0 && (
              <div className="result-sources mt-4">
                <h4>Related Entities</h4>
                <div>
                  {result.entities.map((entity, i) => (
                    <span key={i} className="source-tag">
                      {entity.name}
                      <span className="badge badge-primary" style={{ marginLeft: '4px' }}>
                        {entity.entity_type}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Example queries */}
        {!result && !loading && (
          <div className="card mt-6">
            <div className="card-header">
              <h3 className="card-title">Example Queries</h3>
            </div>
            <div className="card-body">
              <div className="grid grid-2">
                {[
                  'What are the key relationships between Company X and Organization Y?',
                  'Show me all activities related to the March 2024 incident',
                  'Who are the main actors involved in the supply chain network?',
                  'What narratives have emerged in the past week?',
                ].map((example, i) => (
                  <button
                    key={i}
                    className="btn btn-secondary"
                    style={{ justifyContent: 'flex-start', textAlign: 'left' }}
                    onClick={() => setQueryText(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
