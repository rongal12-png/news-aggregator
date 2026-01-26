'use client';

import { useEffect, useState } from 'react';

interface Source {
  id: number;
  name: string;
  feed_url: string;
  language: string;
  category: string;
  weight: number;
  is_active: boolean;
  last_fetched_at: string | null;
  article_count: number;
  recent_articles_24h: number;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('');

  const [formData, setFormData] = useState({
    name: '',
    feed_url: '',
    category: 'general',
    language: 'en',
    weight: 1.0,
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchSources();
  }, [filterCategory]);

  async function fetchSources() {
    try {
      let url = `${API_URL}/admin/sources?include_inactive=true`;
      if (filterCategory) url += `&category=${filterCategory}`;
      const res = await fetch(url);
      const data = await res.json();
      setSources(data.sources);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editingSource) {
        await fetch(`${API_URL}/admin/sources/${editingSource.id}?${new URLSearchParams({
          name: formData.name,
          feed_url: formData.feed_url,
          category: formData.category,
          language: formData.language,
          weight: String(formData.weight),
        })}`, { method: 'PUT' });
      } else {
        await fetch(`${API_URL}/admin/sources?${new URLSearchParams({
          name: formData.name,
          feed_url: formData.feed_url,
          category: formData.category,
          language: formData.language,
          weight: String(formData.weight),
        })}`, { method: 'POST' });
      }
      setShowModal(false);
      setEditingSource(null);
      setFormData({ name: '', feed_url: '', category: 'general', language: 'en', weight: 1.0 });
      fetchSources();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  async function toggleSource(source: Source) {
    try {
      await fetch(`${API_URL}/admin/sources/${source.id}?is_active=${!source.is_active}`, {
        method: 'PUT',
      });
      fetchSources();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  async function deleteSource(source: Source) {
    if (!confirm(`Delete source "${source.name}"? This will also delete all its articles.`)) return;
    try {
      await fetch(`${API_URL}/admin/sources/${source.id}`, { method: 'DELETE' });
      fetchSources();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  function openEdit(source: Source) {
    setEditingSource(source);
    setFormData({
      name: source.name,
      feed_url: source.feed_url,
      category: source.category,
      language: source.language,
      weight: source.weight,
    });
    setShowModal(true);
  }

  const categories = ['general', 'tech', 'crypto', 'finance', 'sports', 'world', 'politics', 'israel'];

  if (loading) {
    return <div><p>Loading...</p></div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h1 className="admin-title">RSS Sources</h1>
          <p className="admin-subtitle">Manage news feed sources</p>
        </div>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowModal(true)}>
          + Add Source
        </button>
      </div>

      <div className="admin-card">
        <div className="admin-card-header">
          <h2 className="admin-card-title">All Sources ({sources.length})</h2>
          <select
            className="form-select"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            style={{ width: 'auto' }}
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Language</th>
              <th>Weight</th>
              <th>Articles</th>
              <th>24h</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id}>
                <td>
                  <div>
                    <strong>{source.name}</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {source.feed_url}
                    </div>
                  </div>
                </td>
                <td style={{ textTransform: 'capitalize' }}>{source.category}</td>
                <td>{source.language === 'en' ? '🇺🇸' : '🇮🇱'} {source.language}</td>
                <td>{source.weight}</td>
                <td>{source.article_count}</td>
                <td>{source.recent_articles_24h}</td>
                <td>
                  <span className={`status-badge ${source.is_active ? 'active' : 'inactive'}`}>
                    {source.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      className="admin-btn admin-btn-secondary admin-btn-sm"
                      onClick={() => openEdit(source)}
                    >
                      Edit
                    </button>
                    <button
                      className="admin-btn admin-btn-secondary admin-btn-sm"
                      onClick={() => toggleSource(source)}
                    >
                      {source.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      className="admin-btn admin-btn-danger admin-btn-sm"
                      onClick={() => deleteSource(source)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{editingSource ? 'Edit Source' : 'Add New Source'}</h2>
            <form className="admin-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Name</label>
                <input
                  className="form-input"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Feed URL</label>
                <input
                  className="form-input"
                  type="url"
                  value={formData.feed_url}
                  onChange={(e) => setFormData({ ...formData, feed_url: e.target.value })}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="form-select"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Language</label>
                  <select
                    className="form-select"
                    value={formData.language}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  >
                    <option value="en">English</option>
                    <option value="he">Hebrew</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Weight (1.0 - 3.0)</label>
                <input
                  className="form-input"
                  type="number"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={formData.weight}
                  onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="admin-btn admin-btn-secondary" onClick={() => {
                  setShowModal(false);
                  setEditingSource(null);
                  setFormData({ name: '', feed_url: '', category: 'general', language: 'en', weight: 1.0 });
                }}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn admin-btn-primary">
                  {editingSource ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
