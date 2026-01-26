'use client';

import { useEffect, useState } from 'react';

interface DailyData {
  date: string;
  views: number;
  unique_visitors: number;
  views_en?: number;
  views_he?: number;
}

interface TopStory {
  story_id: number;
  title: string;
  views: number;
  category: string;
  published_at: string;
}

export default function AnalyticsPage() {
  const [dailyData, setDailyData] = useState<DailyData[]>([]);
  const [topStories, setTopStories] = useState<TopStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  async function fetchAnalytics() {
    setLoading(true);
    try {
      const [dailyRes, storiesRes] = await Promise.all([
        fetch(`${API_URL}/admin/analytics/daily?days=${days}`),
        fetch(`${API_URL}/admin/analytics/top-stories?days=${days}&limit=10`),
      ]);
      const dailyJson = await dailyRes.json();
      const storiesJson = await storiesRes.json();
      setDailyData(dailyJson.days || []);
      setTopStories(storiesJson.top_stories || []);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  }

  const totalViews = dailyData.reduce((sum, d) => sum + d.views, 0);
  const totalUnique = dailyData.reduce((sum, d) => sum + d.unique_visitors, 0);
  const avgDaily = dailyData.length > 0 ? Math.round(totalViews / dailyData.length) : 0;

  if (loading) {
    return <div><p>Loading...</p></div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h1 className="admin-title">Analytics</h1>
          <p className="admin-subtitle">Traffic and engagement metrics</p>
        </div>
        <select
          className="form-select"
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          style={{ width: 'auto' }}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      <div className="stats-grid">
        <div className="stat-card highlight">
          <div className="stat-label">Total Views ({days} days)</div>
          <div className="stat-value">{totalViews.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Unique Visitors</div>
          <div className="stat-value">{totalUnique.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Daily Views</div>
          <div className="stat-value">{avgDaily.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Days Tracked</div>
          <div className="stat-value">{dailyData.length}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">Daily Traffic</h2>
          </div>
          {dailyData.length > 0 ? (
            <div>
              {/* Simple bar chart */}
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '200px', padding: '20px 0' }}>
                {dailyData.map((day, i) => {
                  const maxViews = Math.max(...dailyData.map(d => d.views), 1);
                  const height = (day.views / maxViews) * 100;
                  return (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <div
                        style={{
                          width: '100%',
                          height: `${height}%`,
                          minHeight: '4px',
                          background: 'var(--accent-gradient)',
                          borderRadius: '4px 4px 0 0',
                          transition: 'height 0.3s'
                        }}
                        title={`${day.date}: ${day.views} views`}
                      />
                      <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', transform: 'rotate(-45deg)', whiteSpace: 'nowrap' }}>
                        {new Date(day.date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  );
                })}
              </div>
              <table className="admin-table" style={{ marginTop: '20px' }}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Views</th>
                    <th>Unique</th>
                  </tr>
                </thead>
                <tbody>
                  {[...dailyData].reverse().map((day) => (
                    <tr key={day.date}>
                      <td>{new Date(day.date).toLocaleDateString()}</td>
                      <td><strong>{day.views.toLocaleString()}</strong></td>
                      <td>{day.unique_visitors.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="chart-container">
              <p>No analytics data yet. Views will be tracked as users visit the site.</p>
            </div>
          )}
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2 className="admin-card-title">Top Stories</h2>
          </div>
          {topStories.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {topStories.map((story, i) => (
                <div
                  key={story.story_id}
                  style={{
                    display: 'flex',
                    gap: '12px',
                    padding: '12px',
                    background: 'var(--bg-hover)',
                    borderRadius: '8px'
                  }}
                >
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: i < 3 ? 'var(--accent-gradient)' : 'var(--border-color)',
                    color: i < 3 ? 'white' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    flexShrink: 0
                  }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      marginBottom: '4px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {story.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {story.views} views • {story.category}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No story view data yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
