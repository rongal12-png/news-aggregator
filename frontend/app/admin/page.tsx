'use client';

import { useEffect, useState, useCallback } from 'react';

interface DashboardStats {
  overview: {
    total_sources: number;
    active_sources: number;
    total_articles: number;
    total_stories: number;
    recent_articles_24h: number;
  };
  traffic: {
    views_today: number;
    views_week: number;
    unique_visitors_today: number;
    views_by_locale: Record<string, number>;
  };
  top_categories: Array<{ category: string; views: number }>;
  sources_by_category: Record<string, number>;
}

interface RefreshSettings {
  enabled: boolean;
  interval_minutes: number;
  presets: Array<{ label: string; value: number }>;
}

interface RefreshStatus {
  isRunning: boolean;
  currentStep: string;
  progress: number;
  lastResult?: {
    success: boolean;
    message: string;
    details?: {
      sources_processed?: number;
      new_articles?: number;
      articles_clustered?: number;
      stories_scored?: number;
      summaries_created?: number;
    };
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus>({
    isRunning: false,
    currentStep: '',
    progress: 0,
  });
  const [refreshSettings, setRefreshSettings] = useState<RefreshSettings | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchStats();
    fetchRefreshSettings();
  }, []);

  async function fetchStats() {
    try {
      const res = await fetch(`${API_URL}/admin/dashboard`);
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchRefreshSettings() {
    try {
      const res = await fetch(`${API_URL}/admin/settings/refresh`);
      const data = await res.json();
      setRefreshSettings(data);
    } catch (error) {
      console.error('Failed to fetch refresh settings:', error);
    }
  }

  async function updateRefreshSettings(enabled?: boolean, intervalMinutes?: number) {
    setSavingSettings(true);
    try {
      const params = new URLSearchParams();
      if (enabled !== undefined) params.set('enabled', String(enabled));
      if (intervalMinutes !== undefined) params.set('interval_minutes', String(intervalMinutes));

      await fetch(`${API_URL}/admin/settings/refresh?${params}`, { method: 'PUT' });
      await fetchRefreshSettings();
    } catch (error) {
      console.error('Failed to update settings:', error);
    } finally {
      setSavingSettings(false);
    }
  }

  const runFullRefresh = useCallback(async () => {
    if (refreshStatus.isRunning) return;

    setRefreshStatus({
      isRunning: true,
      currentStep: 'מתחיל...',
      progress: 0,
    });

    try {
      // Step 1: Fetch feeds
      setRefreshStatus({
        isRunning: true,
        currentStep: 'מוריד כתבות ממקורות...',
        progress: 10,
      });

      const fetchRes = await fetch(`${API_URL}/admin/tasks/fetch`, { method: 'POST' });
      const fetchData = await fetchRes.json();

      // Wait for fetch to complete (poll or just wait)
      await new Promise(resolve => setTimeout(resolve, 5000));

      setRefreshStatus({
        isRunning: true,
        currentStep: 'מקבץ כתבות דומות...',
        progress: 40,
      });

      // Step 2: Cluster
      const clusterRes = await fetch(`${API_URL}/admin/tasks/cluster`, { method: 'POST' });
      await clusterRes.json();

      await new Promise(resolve => setTimeout(resolve, 3000));

      setRefreshStatus({
        isRunning: true,
        currentStep: 'יוצר סיכומים...',
        progress: 70,
      });

      // Step 3: Summarize
      const summarizeRes = await fetch(`${API_URL}/admin/tasks/summarize`, { method: 'POST' });
      await summarizeRes.json();

      await new Promise(resolve => setTimeout(resolve, 3000));

      setRefreshStatus({
        isRunning: false,
        currentStep: '',
        progress: 100,
        lastResult: {
          success: true,
          message: 'הרענון הושלם בהצלחה!',
        },
      });

      // Refresh stats
      fetchStats();
    } catch (error) {
      setRefreshStatus({
        isRunning: false,
        currentStep: '',
        progress: 0,
        lastResult: {
          success: false,
          message: `שגיאה: ${error}`,
        },
      });
    }
  }, [API_URL, refreshStatus.isRunning]);

  async function clearSummaries() {
    if (!confirm('האם אתה בטוח שברצונך למחוק את כל הסיכומים? הם יווצרו מחדש לפי דרישה.')) return;
    try {
      const res = await fetch(`${API_URL}/admin/cache/summaries`, { method: 'DELETE' });
      const data = await res.json();
      alert(data.message);
    } catch (error) {
      alert(`שגיאה: ${error}`);
    }
  }

  if (loading) {
    return <div className="admin-main"><p>טוען...</p></div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h1 className="admin-title">לוח בקרה</h1>
          <p className="admin-subtitle">סקירה כללית של אגרגטור החדשות Briefer</p>
        </div>
      </div>

      {/* Main Refresh Card */}
      <div className="admin-card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, var(--bg-card) 0%, var(--accent-light) 100%)' }}>
        <div className="admin-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="admin-card-title">🔄 רענון תוכן</h2>
          {refreshSettings && (
            <span style={{
              fontSize: '0.8125rem',
              color: refreshSettings.enabled ? 'var(--success-color)' : 'var(--text-muted)',
              background: refreshSettings.enabled ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-hover)',
              padding: '4px 12px',
              borderRadius: '16px'
            }}>
              {refreshSettings.enabled
                ? `רענון אוטומטי כל ${refreshSettings.interval_minutes} דקות`
                : 'רענון אוטומטי כבוי'}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {/* Refresh Button */}
          <div style={{ flex: '1', minWidth: '280px' }}>
            <button
              className="admin-btn admin-btn-primary"
              onClick={runFullRefresh}
              disabled={refreshStatus.isRunning}
              style={{
                width: '100%',
                padding: '16px 24px',
                fontSize: '1rem',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
              }}
            >
              {refreshStatus.isRunning ? (
                <>
                  <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span>
                  {refreshStatus.currentStep}
                </>
              ) : (
                <>
                  <span style={{ fontSize: '1.25rem' }}>🚀</span>
                  רענן עכשיו
                </>
              )}
            </button>

            {/* Progress bar */}
            {refreshStatus.isRunning && (
              <div style={{ marginTop: '12px' }}>
                <div style={{
                  height: '6px',
                  background: 'var(--bg-hover)',
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${refreshStatus.progress}%`,
                    background: 'var(--accent-color)',
                    borderRadius: '3px',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            )}

            {/* Last result */}
            {refreshStatus.lastResult && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: refreshStatus.lastResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                borderRadius: '8px',
                color: refreshStatus.lastResult.success ? 'var(--success-color)' : 'var(--error-color)',
                fontSize: '0.875rem'
              }}>
                {refreshStatus.lastResult.success ? '✓' : '✗'} {refreshStatus.lastResult.message}
              </div>
            )}

            <p style={{ marginTop: '12px', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              לחיצה על הכפתור תוריד כתבות חדשות מכל המקורות, תקבץ כתבות דומות לסיפורים, ותיצור סיכומים אוטומטיים.
            </p>
          </div>

          {/* Auto-refresh Settings */}
          <div style={{
            flex: '1',
            minWidth: '280px',
            padding: '16px',
            background: 'var(--bg-card)',
            borderRadius: '12px',
            border: '1px solid var(--border-color)'
          }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '0.9375rem', fontWeight: '600' }}>
              ⏰ רענון אוטומטי
            </h3>

            {refreshSettings && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={refreshSettings.enabled}
                      onChange={(e) => updateRefreshSettings(e.target.checked)}
                      disabled={savingSettings}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '0.875rem' }}>הפעל רענון אוטומטי</span>
                  </label>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <label style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    תדירות:
                  </label>
                  <select
                    value={refreshSettings.interval_minutes}
                    onChange={(e) => updateRefreshSettings(undefined, parseInt(e.target.value))}
                    disabled={savingSettings || !refreshSettings.enabled}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-card)',
                      color: 'var(--text-primary)',
                      fontSize: '0.875rem',
                      cursor: refreshSettings.enabled ? 'pointer' : 'not-allowed',
                      opacity: refreshSettings.enabled ? 1 : 0.5
                    }}
                  >
                    {refreshSettings.presets.map((preset) => (
                      <option key={preset.value} value={preset.value}>
                        {preset.label}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card highlight">
          <div className="stat-label">צפיות היום</div>
          <div className="stat-value">{stats?.traffic.views_today.toLocaleString() || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">מבקרים ייחודיים</div>
          <div className="stat-value">{stats?.traffic.unique_visitors_today.toLocaleString() || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">צפיות השבוע</div>
          <div className="stat-value">{stats?.traffic.views_week.toLocaleString() || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">סיפורים פעילים</div>
          <div className="stat-value">{stats?.overview.total_stories.toLocaleString() || 0}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">סקירת תוכן</h2>
          </div>
          <table className="admin-table">
            <tbody>
              <tr>
                <td>סה"כ מקורות</td>
                <td><strong>{stats?.overview.total_sources}</strong></td>
              </tr>
              <tr>
                <td>מקורות פעילים</td>
                <td><strong>{stats?.overview.active_sources}</strong></td>
              </tr>
              <tr>
                <td>סה"כ כתבות</td>
                <td><strong>{stats?.overview.total_articles.toLocaleString()}</strong></td>
              </tr>
              <tr>
                <td>כתבות (24 שעות)</td>
                <td><strong>{stats?.overview.recent_articles_24h}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">תנועה לפי שפה</h2>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>שפה</th>
                <th>צפיות היום</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats?.traffic.views_by_locale || {}).map(([locale, views]) => (
                <tr key={locale}>
                  <td>{locale === 'en' ? '🇺🇸 אנגלית' : '🇮🇱 עברית'}</td>
                  <td><strong>{views}</strong></td>
                </tr>
              ))}
              {Object.keys(stats?.traffic.views_by_locale || {}).length === 0 && (
                <tr>
                  <td colSpan={2} style={{ color: 'var(--text-muted)' }}>אין נתונים עדיין</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">מקורות לפי קטגוריה</h2>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>קטגוריה</th>
                <th>מקורות</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats?.sources_by_category || {}).map(([cat, count]) => (
                <tr key={cat}>
                  <td style={{ textTransform: 'capitalize' }}>{cat}</td>
                  <td><strong>{count}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">קטגוריות מובילות היום</h2>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>קטגוריה</th>
                <th>צפיות</th>
              </tr>
            </thead>
            <tbody>
              {stats?.top_categories.map((item) => (
                <tr key={item.category}>
                  <td style={{ textTransform: 'capitalize' }}>{item.category}</td>
                  <td><strong>{item.views}</strong></td>
                </tr>
              ))}
              {(stats?.top_categories.length === 0) && (
                <tr>
                  <td colSpan={2} style={{ color: 'var(--text-muted)' }}>אין נתונים עדיין</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="admin-card">
        <div className="admin-card-header">
          <h2 className="admin-card-title">פעולות מערכת</h2>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button className="admin-btn admin-btn-danger" onClick={clearSummaries}>
            🗑️ מחק את כל הסיכומים
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
