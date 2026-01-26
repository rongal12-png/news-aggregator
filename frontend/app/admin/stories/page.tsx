'use client';

import { useState, useEffect } from 'react';

interface Story {
  id: number;
  title: string;
  topic: string | null;
  tags: string[];
  score: number;
  article_count: number;
  created_at: string;
  updated_at: string | null;
  is_new: boolean;
}

interface StoryStats {
  total_stories: number;
  stories_by_topic: Record<string, number>;
  recent_activity: {
    stories_last_24h: number;
    articles_last_24h: number;
  };
  avg_articles_per_story: number;
}

type SortField = 'time' | 'topic' | 'score';
type SortOrder = 'asc' | 'desc';

export default function AdminStoriesPage() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const [stories, setStories] = useState<Story[]>([]);
  const [stats, setStats] = useState<StoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [total, setTotal] = useState(0);

  // Filters and sorting
  const [sortField, setSortField] = useState<SortField>('time');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [filterTopic, setFilterTopic] = useState('');
  const [showOnlyNew, setShowOnlyNew] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Calculate since time for "new" stories (last 24 hours)
  const getSinceTime = () => {
    const since = new Date();
    since.setHours(since.getHours() - 24);
    return since.toISOString();
  };

  // Fetch stories
  const fetchStories = async () => {
    try {
      setLoading(true);
      setError('');

      const params = new URLSearchParams({
        sort_by: sortField,
        order: sortOrder,
        limit: itemsPerPage.toString(),
        offset: ((currentPage - 1) * itemsPerPage).toString(),
        since: getSinceTime(), // For marking new stories
      });

      if (filterTopic) {
        params.append('topic', filterTopic);
      }

      const response = await fetch(`${API_URL}/admin/stories?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch stories');
      }

      const data = await response.json();
      setStories(data.stories || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stories');
    } finally {
      setLoading(false);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/stories/stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  useEffect(() => {
    fetchStories();
  }, [sortField, sortOrder, filterTopic, showOnlyNew, currentPage]);

  useEffect(() => {
    fetchStats();
  }, []);

  // Delete story
  const handleDelete = async (id: number) => {
    try {
      setDeleting(true);
      setDeleteError('');

      const response = await fetch(`${API_URL}/admin/stories/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete story');
      }

      setSuccessMessage('הסיפור נמחק בהצלחה');
      setDeleteConfirm(null);

      // Refresh data
      await fetchStories();
      await fetchStats();

      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete story');
    } finally {
      setDeleting(false);
    }
  };

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const allTopics = stats ? Object.keys(stats.stories_by_topic).sort() : [];
  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));

  // Filter stories if showing only new
  const displayedStories = showOnlyNew ? stories.filter(s => s.is_new) : stories;

  return (
    <div className="admin-content">
      {/* Header */}
      <div className="admin-header">
        <h1>ניהול סיפורים</h1>
        <p>צפייה ומחיקה של סיפורים חדשותיים</p>
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="alert alert-success">
          {successMessage}
        </div>
      )}
      {deleteError && (
        <div className="alert alert-error">
          {deleteError}
        </div>
      )}
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Statistics */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">סך הכל סיפורים</div>
            <div className="stat-value">{stats.total_stories}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">24 שעות אחרונות</div>
            <div className="stat-value">{stats.recent_activity.stories_last_24h}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">ממוצע כתבות לסיפור</div>
            <div className="stat-value">{stats.avg_articles_per_story.toFixed(1)}</div>
          </div>
          <div className="stat-card topics-card">
            <div className="stat-label">נושאים</div>
            <div className="topics-list">
              {Object.entries(stats.stories_by_topic).map(([topic, count]) => (
                <div key={topic} className="topic-item">
                  <span>{topic || 'ללא נושא'}</span>
                  <span className="topic-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="filters-card">
        <div className="filters-grid">
          {/* Sort buttons */}
          <div>
            <label className="filter-label">מיין לפי</label>
            <div className="button-group">
              <button
                onClick={() => toggleSort('time')}
                className={`btn ${sortField === 'time' ? 'btn-primary' : 'btn-secondary'}`}
              >
                זמן {sortField === 'time' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <button
                onClick={() => toggleSort('topic')}
                className={`btn ${sortField === 'topic' ? 'btn-primary' : 'btn-secondary'}`}
              >
                נושא {sortField === 'topic' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <button
                onClick={() => toggleSort('score')}
                className={`btn ${sortField === 'score' ? 'btn-primary' : 'btn-secondary'}`}
              >
                ציון {sortField === 'score' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
            </div>
          </div>

          {/* Topic filter */}
          <div>
            <label className="filter-label">סנן לפי נושא</label>
            <select
              value={filterTopic}
              onChange={(e) => {
                setFilterTopic(e.target.value);
                setCurrentPage(1);
              }}
              className="select-input"
            >
              <option value="">כל הנושאים</option>
              {allTopics.map((topic) => (
                <option key={topic} value={topic}>
                  {topic || 'ללא נושא'}
                </option>
              ))}
            </select>
          </div>

          {/* Show only new */}
          <div className="checkbox-wrapper">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showOnlyNew}
                onChange={(e) => {
                  setShowOnlyNew(e.target.checked);
                  setCurrentPage(1);
                }}
                className="checkbox-input"
              />
              <span>הצג רק סיפורים חדשים</span>
            </label>
          </div>

          {/* Refresh */}
          <div className="refresh-wrapper">
            <button
              onClick={() => {
                fetchStories();
                fetchStats();
              }}
              className="btn btn-secondary"
            >
              רענן
            </button>
          </div>
        </div>
      </div>

      {/* Stories Table */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>טוען סיפורים...</p>
        </div>
      ) : displayedStories.length === 0 ? (
        <div className="empty-state">
          <p>לא נמצאו סיפורים</p>
        </div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="stories-table-wrapper desktop-only">
            <table className="stories-table">
              <thead>
                <tr>
                  <th>כותרת</th>
                  <th>נושא</th>
                  <th>ציון</th>
                  <th>כתבות</th>
                  <th>תאריך</th>
                  <th>פעולות</th>
                </tr>
              </thead>
              <tbody>
                {displayedStories.map((story) => (
                  <tr key={story.id}>
                    <td>
                      <div className="story-title-cell">
                        <a
                          href={`/story/${story.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="story-title-link"
                          title="פתח סיפור בחלון חדש"
                        >
                          {story.title || `סיפור #${story.id}`}
                        </a>
                        {story.is_new && (
                          <span className="badge badge-new">חדש</span>
                        )}
                      </div>
                      {story.tags.length > 0 && (
                        <div className="tags-container">
                          {story.tags.map((tag, idx) => (
                            <span key={idx} className="tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>{story.topic || '—'}</td>
                    <td className="score-cell">{story.score.toFixed(2)}</td>
                    <td>{story.article_count}</td>
                    <td className="date-cell">
                      {new Date(story.created_at).toLocaleDateString('he-IL', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td>
                      <button
                        onClick={() => setDeleteConfirm(story.id)}
                        className="btn btn-danger btn-sm"
                      >
                        מחק
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="stories-cards mobile-only">
            {displayedStories.map((story) => (
              <div key={story.id} className="story-card">
                <div className="story-card-header">
                  <a
                    href={`/story/${story.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="story-card-title story-title-link"
                  >
                    {story.title || `סיפור #${story.id}`}
                  </a>
                  {story.is_new && (
                    <span className="badge badge-new">חדש</span>
                  )}
                </div>
                {story.tags.length > 0 && (
                  <div className="tags-container">
                    {story.tags.map((tag, idx) => (
                      <span key={idx} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                <div className="story-card-details">
                  <div className="detail-item">
                    <span className="detail-label">נושא:</span>
                    <span>{story.topic || '—'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">ציון:</span>
                    <span className="score-value">{story.score.toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">כתבות:</span>
                    <span>{story.article_count}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">תאריך:</span>
                    <span className="date-value">
                      {new Date(story.created_at).toLocaleDateString('he-IL', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setDeleteConfirm(story.id)}
                  className="btn btn-danger btn-block"
                >
                  מחק סיפור
                </button>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="btn btn-secondary"
              >
                הקודם
              </button>
              <span className="page-info">
                עמוד {currentPage} מתוך {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="btn btn-secondary"
              >
                הבא
              </button>
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm !== null && (
        <div className="modal-overlay">
          <div className="modal">
            <h3 className="modal-title">אישור מחיקה</h3>
            <p className="modal-text">
              האם אתה בטוח שברצונך למחוק את הסיפור הזה? פעולה זו אינה הפיכה.
            </p>
            <div className="modal-actions">
              <button
                onClick={() => setDeleteConfirm(null)}
                disabled={deleting}
                className="btn btn-secondary"
              >
                ביטול
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                disabled={deleting}
                className="btn btn-danger"
              >
                {deleting ? 'מוחק...' : 'מחק'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
