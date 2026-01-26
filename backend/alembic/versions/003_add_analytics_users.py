"""Add analytics, categories, system settings, and user tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Page views table for analytics
    op.create_table(
        'page_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('locale', sa.String(length=10), server_default='en'),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pageviews_created', 'page_views', ['created_at'])
    op.create_index('idx_pageviews_path', 'page_views', ['path'])
    op.create_index('idx_pageviews_story', 'page_views', ['story_id'])

    # Daily stats table for aggregated analytics
    op.create_table(
        'daily_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_views', sa.Integer(), server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), server_default='0'),
        sa.Column('views_en', sa.Integer(), server_default='0'),
        sa.Column('views_he', sa.Integer(), server_default='0'),
        sa.Column('top_stories', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('top_categories', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index('idx_daily_stats_date', 'daily_stats', ['date'])

    # Categories table for dynamic category management
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('name_he', sa.String(length=100), nullable=False),
        sa.Column('icon', sa.String(length=10), server_default='📰'),
        sa.Column('color', sa.String(length=20), server_default='#6b7280'),
        sa.Column('sort_order', sa.Integer(), server_default='100'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('locale_filter', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # System settings table for configuration
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Users table for authentication
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('provider', sa.String(length=50), server_default='email'),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_admin', sa.Boolean(), server_default='false'),
        sa.Column('locale', sa.String(length=10), server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # User sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('idx_sessions_token', 'user_sessions', ['token'])

    # Favorites table
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'story_id', name='uq_user_story_favorite')
    )
    op.create_index('idx_favorites_user', 'favorites', ['user_id'])
    op.create_index('idx_favorites_story', 'favorites', ['story_id'])


def downgrade() -> None:
    op.drop_table('favorites')
    op.drop_table('user_sessions')
    op.drop_table('users')
    op.drop_table('system_settings')
    op.drop_table('categories')
    op.drop_table('daily_stats')
    op.drop_table('page_views')
