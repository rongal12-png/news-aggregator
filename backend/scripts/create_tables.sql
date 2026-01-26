-- Create missing tables for analytics, settings, and users
-- Run this SQL directly on your PostgreSQL database if you're not using Alembic

-- Page views table for analytics
CREATE TABLE IF NOT EXISTS page_views (
    id SERIAL PRIMARY KEY,
    path VARCHAR(500) NOT NULL,
    locale VARCHAR(10) DEFAULT 'en',
    story_id INTEGER,
    category VARCHAR(50),
    user_agent VARCHAR(500),
    ip_hash VARCHAR(64),
    referrer VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pageviews_created ON page_views(created_at);
CREATE INDEX IF NOT EXISTS idx_pageviews_path ON page_views(path);
CREATE INDEX IF NOT EXISTS idx_pageviews_story ON page_views(story_id);

-- Daily stats table for aggregated analytics
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    views_en INTEGER DEFAULT 0,
    views_he INTEGER DEFAULT 0,
    top_stories JSONB DEFAULT '[]',
    top_categories JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);

-- Categories table for dynamic category management
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) NOT NULL UNIQUE,
    name_en VARCHAR(100) NOT NULL,
    name_he VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📰',
    color VARCHAR(20) DEFAULT '#6b7280',
    sort_order INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    locale_filter VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- System settings table for configuration
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value VARCHAR(500),
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    provider VARCHAR(50) DEFAULT 'email',
    provider_id VARCHAR(255),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    locale VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    last_login_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token);

-- Favorites table
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE(user_id, story_id)
);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_story ON favorites(story_id);

-- Insert default categories
INSERT INTO categories (slug, name_en, name_he, icon, color, sort_order, locale_filter) VALUES
    ('all', 'All', 'הכל', '🌐', '#6b7280', 0, NULL),
    ('israel', 'Israel', 'ישראל', '🇮🇱', '#0066cc', 5, 'he'),
    ('world', 'World', 'עולם', '🌍', '#0ea5e9', 10, NULL),
    ('politics', 'Politics', 'פוליטיקה', '🏛️', '#8b5cf6', 20, NULL),
    ('tech', 'Technology', 'טכנולוגיה', '💻', '#3b82f6', 30, NULL),
    ('finance', 'Finance', 'כלכלה', '📈', '#10b981', 40, NULL),
    ('crypto', 'Crypto', 'קריפטו', '₿', '#f59e0b', 50, NULL),
    ('sports', 'Sports', 'ספורט', '⚽', '#ef4444', 60, NULL),
    ('general', 'General', 'כללי', '📰', '#6b7280', 100, NULL)
ON CONFLICT (slug) DO NOTHING;

-- Insert default settings
INSERT INTO system_settings (key, value) VALUES
    ('refresh_enabled', 'true'),
    ('refresh_interval_minutes', '60')
ON CONFLICT (key) DO NOTHING;
