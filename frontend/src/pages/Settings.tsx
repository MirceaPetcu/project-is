import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Server, Check, X, RefreshCw } from 'lucide-react';
import { healthCheck, getApiInfo } from '../api/client';

export default function Settings() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'disconnected'>(
    'checking'
  );
  const [apiInfo, setApiInfo] = useState<{
    name: string;
    version: string;
    description: string;
  } | null>(null);
  const [settings, setSettings] = useState({
    defaultQueryMode: 'hybrid',
    minCredibility: '0.3',
    onlyCredibleSources: true,
    autoRefreshAlerts: true,
    refreshInterval: '30',
  });

  useEffect(() => {
    checkApiStatus();
  }, []);

  async function checkApiStatus() {
    setApiStatus('checking');
    try {
      await healthCheck();
      const info = await getApiInfo();
      setApiInfo(info);
      setApiStatus('connected');
    } catch (err) {
      console.error('API check failed:', err);
      setApiStatus('disconnected');
    }
  }

  const handleSettingChange = (key: string, value: string | boolean) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <>
      <header className="content-header">
        <h1>Settings</h1>
        <p>Configure platform preferences</p>
      </header>

      <div className="content-body">
        {/* API Status */}
        <div className="card mb-6">
          <div className="card-header">
            <h3 className="card-title flex items-center gap-2">
              <Server size={16} />
              API Connection
            </h3>
            <button className="btn btn-ghost btn-sm" onClick={checkApiStatus}>
              <RefreshCw
                size={14}
                className={apiStatus === 'checking' ? 'spinner' : ''}
              />
            </button>
          </div>
          <div className="card-body">
            <div className="flex items-center gap-4">
              <div
                className={`flex items-center gap-2 ${
                  apiStatus === 'connected'
                    ? 'text-success'
                    : apiStatus === 'disconnected'
                    ? 'text-danger'
                    : 'text-muted'
                }`}
                style={{
                  color:
                    apiStatus === 'connected'
                      ? 'var(--accent-success)'
                      : apiStatus === 'disconnected'
                      ? 'var(--accent-danger)'
                      : 'var(--text-muted)',
                }}
              >
                {apiStatus === 'connected' ? (
                  <Check size={20} />
                ) : apiStatus === 'disconnected' ? (
                  <X size={20} />
                ) : (
                  <RefreshCw size={20} className="spinner" />
                )}
                <span style={{ fontWeight: 500 }}>
                  {apiStatus === 'connected'
                    ? 'Connected'
                    : apiStatus === 'disconnected'
                    ? 'Disconnected'
                    : 'Checking...'}
                </span>
              </div>

              {apiInfo && (
                <div className="text-sm text-muted">
                  {apiInfo.name} v{apiInfo.version}
                </div>
              )}
            </div>

            {apiStatus === 'disconnected' && (
              <div className="alert alert-warning mt-4">
                <div className="alert-content">
                  <div className="alert-title">Backend not available</div>
                  <p>
                    Make sure the FastAPI backend is running on port 8000. The UI
                    will display demo data until connected.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Query Settings */}
        <div className="card mb-6">
          <div className="card-header">
            <h3 className="card-title">Query Defaults</h3>
          </div>
          <div className="card-body">
            <div className="grid grid-2" style={{ gap: '24px' }}>
              <div className="input-group">
                <label className="input-label">Default Query Mode</label>
                <select
                  className="input"
                  value={settings.defaultQueryMode}
                  onChange={(e) => handleSettingChange('defaultQueryMode', e.target.value)}
                >
                  <option value="hybrid">Hybrid</option>
                  <option value="local">Local</option>
                  <option value="global">Global</option>
                  <option value="naive">Naive</option>
                </select>
              </div>

              <div className="input-group">
                <label className="input-label">Minimum Credibility</label>
                <select
                  className="input"
                  value={settings.minCredibility}
                  onChange={(e) => handleSettingChange('minCredibility', e.target.value)}
                >
                  <option value="0">Any</option>
                  <option value="0.3">30%+</option>
                  <option value="0.5">50%+</option>
                  <option value="0.7">70%+</option>
                </select>
              </div>

              <div className="input-group">
                <label
                  className="input-label"
                  style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <input
                    type="checkbox"
                    checked={settings.onlyCredibleSources}
                    onChange={(e) =>
                      handleSettingChange('onlyCredibleSources', e.target.checked)
                    }
                    style={{ width: '18px', height: '18px' }}
                  />
                  Only credible sources by default
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Alert Settings */}
        <div className="card mb-6">
          <div className="card-header">
            <h3 className="card-title">Alert Settings</h3>
          </div>
          <div className="card-body">
            <div className="grid grid-2" style={{ gap: '24px' }}>
              <div className="input-group">
                <label
                  className="input-label"
                  style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <input
                    type="checkbox"
                    checked={settings.autoRefreshAlerts}
                    onChange={(e) =>
                      handleSettingChange('autoRefreshAlerts', e.target.checked)
                    }
                    style={{ width: '18px', height: '18px' }}
                  />
                  Auto-refresh alerts
                </label>
              </div>

              <div className="input-group">
                <label className="input-label">Refresh Interval (seconds)</label>
                <select
                  className="input"
                  value={settings.refreshInterval}
                  onChange={(e) => handleSettingChange('refreshInterval', e.target.value)}
                  disabled={!settings.autoRefreshAlerts}
                >
                  <option value="15">15 seconds</option>
                  <option value="30">30 seconds</option>
                  <option value="60">1 minute</option>
                  <option value="300">5 minutes</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title flex items-center gap-2">
              <SettingsIcon size={16} />
              About
            </h3>
          </div>
          <div className="card-body">
            <div className="flex flex-col gap-4">
              <div>
                <span className="text-muted">Platform</span>
                <p style={{ fontWeight: 500 }}>OSINT Intelligence Platform</p>
              </div>
              <div>
                <span className="text-muted">UI Version</span>
                <p>1.0.0</p>
              </div>
              <div>
                <span className="text-muted">Description</span>
                <p>
                  Multi-source OSINT intelligence platform with advanced entity
                  resolution, narrative detection, temporal analysis, and geographic
                  intelligence capabilities.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
