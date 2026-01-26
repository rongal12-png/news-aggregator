'use client';

import { useEffect, useState } from 'react';

interface Category {
  id?: number;
  slug: string;
  name_en: string;
  name_he: string;
  icon: string;
  color: string;
  sort_order: number;
  is_active: boolean;
  locale_filter: string | null;
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);

  const [formData, setFormData] = useState({
    slug: '',
    name_en: '',
    name_he: '',
    icon: '📰',
    color: '#6b7280',
    sort_order: 100,
    locale_filter: '',
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchCategories();
  }, []);

  async function fetchCategories() {
    try {
      const res = await fetch(`${API_URL}/admin/categories`);
      const data = await res.json();
      setCategories(data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const params = new URLSearchParams({
        slug: formData.slug,
        name_en: formData.name_en,
        name_he: formData.name_he,
        icon: formData.icon,
        color: formData.color,
        sort_order: String(formData.sort_order),
        locale_filter: formData.locale_filter,
      });

      if (editingCategory?.id) {
        await fetch(`${API_URL}/admin/categories/${editingCategory.id}?${params}`, { method: 'PUT' });
      } else {
        await fetch(`${API_URL}/admin/categories?${params}`, { method: 'POST' });
      }
      setShowModal(false);
      setEditingCategory(null);
      resetForm();
      fetchCategories();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  async function toggleCategory(category: Category) {
    if (!category.id) return;
    try {
      await fetch(`${API_URL}/admin/categories/${category.id}?is_active=${!category.is_active}`, {
        method: 'PUT',
      });
      fetchCategories();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  async function deleteCategory(category: Category) {
    if (!category.id) {
      alert('Cannot delete default categories');
      return;
    }
    if (!confirm(`Delete category "${category.name_en}"?`)) return;
    try {
      await fetch(`${API_URL}/admin/categories/${category.id}`, { method: 'DELETE' });
      fetchCategories();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  function openEdit(category: Category) {
    setEditingCategory(category);
    setFormData({
      slug: category.slug,
      name_en: category.name_en,
      name_he: category.name_he,
      icon: category.icon,
      color: category.color,
      sort_order: category.sort_order,
      locale_filter: category.locale_filter || '',
    });
    setShowModal(true);
  }

  function resetForm() {
    setFormData({
      slug: '',
      name_en: '',
      name_he: '',
      icon: '📰',
      color: '#6b7280',
      sort_order: 100,
      locale_filter: '',
    });
  }

  if (loading) {
    return <div><p>Loading...</p></div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h1 className="admin-title">Categories</h1>
          <p className="admin-subtitle">Manage news categories</p>
        </div>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowModal(true)}>
          + Add Category
        </button>
      </div>

      <div className="admin-card">
        <div className="admin-card-header">
          <h2 className="admin-card-title">All Categories ({categories.length})</h2>
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Icon</th>
              <th>Slug</th>
              <th>English Name</th>
              <th>Hebrew Name</th>
              <th>Color</th>
              <th>Order</th>
              <th>Locale</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category) => (
              <tr key={category.slug}>
                <td style={{ fontSize: '1.5rem' }}>{category.icon}</td>
                <td><code>{category.slug}</code></td>
                <td>{category.name_en}</td>
                <td>{category.name_he}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="color-dot" style={{ background: category.color }}></span>
                    <code>{category.color}</code>
                  </div>
                </td>
                <td>{category.sort_order}</td>
                <td>
                  {category.locale_filter === 'he' && '🇮🇱 Hebrew only'}
                  {category.locale_filter === 'en' && '🇺🇸 English only'}
                  {!category.locale_filter && '🌐 All'}
                </td>
                <td>
                  <span className={`status-badge ${category.is_active ? 'active' : 'inactive'}`}>
                    {category.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      className="admin-btn admin-btn-secondary admin-btn-sm"
                      onClick={() => openEdit(category)}
                    >
                      Edit
                    </button>
                    {category.id && (
                      <>
                        <button
                          className="admin-btn admin-btn-secondary admin-btn-sm"
                          onClick={() => toggleCategory(category)}
                        >
                          {category.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          className="admin-btn admin-btn-danger admin-btn-sm"
                          onClick={() => deleteCategory(category)}
                        >
                          Delete
                        </button>
                      </>
                    )}
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
            <h2 className="modal-title">{editingCategory ? 'Edit Category' : 'Add New Category'}</h2>
            <form className="admin-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Slug (unique identifier)</label>
                <input
                  className="form-input"
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') })}
                  required
                  disabled={!!editingCategory}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">English Name</label>
                  <input
                    className="form-input"
                    type="text"
                    value={formData.name_en}
                    onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Hebrew Name</label>
                  <input
                    className="form-input"
                    type="text"
                    value={formData.name_he}
                    onChange={(e) => setFormData({ ...formData, name_he: e.target.value })}
                    required
                    dir="rtl"
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Icon (emoji)</label>
                  <input
                    className="form-input"
                    type="text"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    maxLength={4}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Color</label>
                  <input
                    className="form-input"
                    type="color"
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    style={{ height: '40px' }}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Sort Order</label>
                  <input
                    className="form-input"
                    type="number"
                    value={formData.sort_order}
                    onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Show in Locale</label>
                  <select
                    className="form-select"
                    value={formData.locale_filter}
                    onChange={(e) => setFormData({ ...formData, locale_filter: e.target.value })}
                  >
                    <option value="">All Languages</option>
                    <option value="en">English Only</option>
                    <option value="he">Hebrew Only</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="admin-btn admin-btn-secondary" onClick={() => {
                  setShowModal(false);
                  setEditingCategory(null);
                  resetForm();
                }}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn admin-btn-primary">
                  {editingCategory ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
