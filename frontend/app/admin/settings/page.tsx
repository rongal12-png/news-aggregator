'use client';

import { useEffect, useState } from 'react';

interface RefreshSettings {
  enabled: boolean;
  interval_minutes: number;
  presets: { label: string; value: number }[];
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<RefreshSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [customInterval, setCustomInterval] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      const res = await fetch(`${API_URL}/admin/settings/refresh`);
      const data = await res.json();
      setSettings(data);
      setCustomInterval(String(data.interval_minutes));
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  }

  async function updateSettings(enabled?: boolean, interval?: number) {
    setSaving(true);
    setMessage(null);
    try {
      const params = new URLSearchParams();
      if (enabled !== undefined) params.append('enabled', String(enabled));
      if (interval !== undefined) params.append('interval_minutes', String(interval));

      const res = await fetch(`${API_URL}/admin/settings/refresh?${params}`, {
        method: 'PUT',
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to update settings');
      }

      await fetchSettings();
      setMessage({ type: 'success', text: 'Settings updated successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: String(error) });
    } finally {
      setSaving(false);
    }
  }

  async function triggerRefresh() {
    setRefreshing(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/admin/tasks/refresh-now`, {
        method: 'POST',
      });
      const data = await res.json();
      setMessage({ type: 'success', text: 'Refresh triggered! Tasks are running in the background.' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to trigger refresh' });
    } finally {
      setRefreshing(false);
    }
  }

  function handlePresetChange(value: number) {
    setCustomInterval(String(value));
    updateSettings(undefined, value);
  }

  function handleCustomIntervalSubmit(e: React.FormEvent) {
    e.preventDefault();
    const interval = parseInt(customInterval);
    if (interval >= 1 && interval <= 10080) {
      updateSettings(undefined, interval);
    } else {
      setMessage({ type: 'error', text: 'Interval must be between 1 and 10080 minutes' });
    }
  }

  if (loading) {
    return <div><p>Loading...</p></div>;
  }

  if (!settings) {
    return <div><p>Failed to load settings</p></div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h1 className="admin-title">Settings</h1>
          <p className="admin-subtitle">Configure system behavior</p>
        </div>
      </div>

      {message && (
        <div className={`admin-alert ${message.type}`} style={{ marginBottom: '20px' }}>
          {message.text}
        </div>
      )}

      <div className="admin-card">
        <div className="admin-card-header">
          <h2 className="admin-card-title">Auto Refresh</h2>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={settings.enabled}
              onChange={(e) => updateSettings(e.target.checked, undefined)}
              disabled={saving}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">{settings.enabled ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="settings-section">
          <h3 className="settings-label">Refresh Interval</h3>
          <p className="settings-description">
            How often to fetch new articles, cluster stories, and generate summaries.
            {!settings.enabled && ' (Auto-refresh is currently disabled)'}
          </p>

          <div className="preset-buttons" style={{ marginTop: '16px', opacity: settings.enabled ? 1 : 0.5 }}>
            {settings.presets.map((preset) => (
              <button
                key={preset.value}
                className={`preset-btn ${settings.interval_minutes === preset.value ? 'active' : ''}`}
                onClick={() => handlePresetChange(preset.value)}
                disabled={saving || !settings.enabled}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleCustomIntervalSubmit} className="custom-interval" style={{ marginTop: '16px' }}>
            <label className="form-label">Custom interval (minutes)</label>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="number"
                className="form-input"
                style={{ width: '120px' }}
                value={customInterval}
                onChange={(e) => setCustomInterval(e.target.value)}
                min="1"
                max="10080"
                disabled={saving || !settings.enabled}
              />
              <button
                type="submit"
                className="admin-btn admin-btn-secondary"
                disabled={saving || !settings.enabled}
              >
                Apply
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: '20px' }}>
        <div className="admin-card-header">
          <h2 className="admin-card-title">Manual Actions</h2>
        </div>

        <div className="settings-section">
          <h3 className="settings-label">Immediate Refresh</h3>
          <p className="settings-description">
            Manually trigger a full refresh cycle: fetch feeds, cluster stories, and generate summaries.
            This works even when auto-refresh is disabled.
          </p>

          <button
            className="admin-btn admin-btn-primary"
            onClick={triggerRefresh}
            disabled={refreshing}
            style={{ marginTop: '16px' }}
          >
            {refreshing ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>

        <div className="settings-section" style={{ marginTop: '24px' }}>
          <h3 className="settings-label">Individual Tasks</h3>
          <p className="settings-description">
            Trigger individual pipeline stages for debugging or maintenance.
          </p>

          <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
            <button
              className="admin-btn admin-btn-secondary"
              onClick={async () => {
                await fetch(`${API_URL}/admin/tasks/fetch`, { method: 'POST' });
                setMessage({ type: 'success', text: 'Fetch task triggered' });
              }}
            >
              Fetch Feeds
            </button>
            <button
              className="admin-btn admin-btn-secondary"
              onClick={async () => {
                await fetch(`${API_URL}/admin/tasks/cluster`, { method: 'POST' });
                setMessage({ type: 'success', text: 'Cluster task triggered' });
              }}
            >
              Cluster Stories
            </button>
            <button
              className="admin-btn admin-btn-secondary"
              onClick={async () => {
                await fetch(`${API_URL}/admin/tasks/summarize`, { method: 'POST' });
                setMessage({ type: 'success', text: 'Summarize task triggered' });
              }}
            >
              Generate Summaries
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .admin-alert {
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 0.9rem;
        }
        .admin-alert.success {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          color: #10b981;
        }
        .admin-alert.error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
        }
        .toggle-switch {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
        }
        .toggle-switch input {
          display: none;
        }
        .toggle-slider {
          width: 48px;
          height: 26px;
          background: var(--border-color, #374151);
          border-radius: 13px;
          position: relative;
          transition: background 0.2s;
        }
        .toggle-slider::after {
          content: '';
          position: absolute;
          width: 20px;
          height: 20px;
          background: white;
          border-radius: 50%;
          top: 3px;
          left: 3px;
          transition: transform 0.2s;
        }
        .toggle-switch input:checked + .toggle-slider {
          background: #3b82f6;
        }
        .toggle-switch input:checked + .toggle-slider::after {
          transform: translateX(22px);
        }
        .toggle-label {
          font-weight: 500;
          color: var(--text-secondary, #9ca3af);
        }
        .settings-section {
          padding: 20px;
          border-top: 1px solid var(--border-color, #374151);
        }
        .settings-label {
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary, #f3f4f6);
          margin: 0 0 8px 0;
        }
        .settings-description {
          font-size: 0.875rem;
          color: var(--text-secondary, #9ca3af);
          margin: 0;
          line-height: 1.5;
        }
        .preset-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .preset-btn {
          padding: 8px 16px;
          border: 1px solid var(--border-color, #374151);
          background: transparent;
          color: var(--text-secondary, #9ca3af);
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.875rem;
          transition: all 0.2s;
        }
        .preset-btn:hover:not(:disabled) {
          border-color: #3b82f6;
          color: #3b82f6;
        }
        .preset-btn.active {
          background: #3b82f6;
          border-color: #3b82f6;
          color: white;
        }
        .preset-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
