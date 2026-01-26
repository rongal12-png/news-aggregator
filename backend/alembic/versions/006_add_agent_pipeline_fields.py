"""Add agent pipeline fields to stories and articles

Revision ID: 006
Revises: 005
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: str = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add agent pipeline fields to stories and articles tables."""

    # Add fields to stories table
    op.add_column('stories', sa.Column('meta_description', sa.Text(), nullable=True))
    op.add_column('stories', sa.Column('og_title', sa.String(length=255), nullable=True))
    op.add_column('stories', sa.Column('og_description', sa.Text(), nullable=True))
    op.add_column('stories', sa.Column('og_image', sa.String(length=500), nullable=True))
    op.add_column('stories', sa.Column('seo_keywords', sa.JSON(), nullable=True))
    op.add_column('stories', sa.Column('country_code', sa.String(length=2), nullable=True))
    op.add_column('stories', sa.Column('is_newsworthy', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('stories', sa.Column('newsworthiness_score', sa.Float(), nullable=True))

    # Create indexes on stories table
    op.create_index('ix_stories_country_code', 'stories', ['country_code'])

    # Add fields to articles table
    op.add_column('articles', sa.Column('is_filtered', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('articles', sa.Column('filter_reason', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('importance_score', sa.Float(), nullable=True))

    # Create indexes on articles table
    op.create_index('ix_articles_is_filtered', 'articles', ['is_filtered'])
    op.create_index('ix_articles_importance_score', 'articles', ['importance_score'])


def downgrade() -> None:
    """Remove agent pipeline fields from stories and articles tables."""

    # Drop indexes from articles table
    op.drop_index('ix_articles_importance_score', table_name='articles')
    op.drop_index('ix_articles_is_filtered', table_name='articles')

    # Drop columns from articles table
    op.drop_column('articles', 'importance_score')
    op.drop_column('articles', 'filter_reason')
    op.drop_column('articles', 'is_filtered')

    # Drop indexes from stories table
    op.drop_index('ix_stories_country_code', table_name='stories')

    # Drop columns from stories table
    op.drop_column('stories', 'newsworthiness_score')
    op.drop_column('stories', 'is_newsworthy')
    op.drop_column('stories', 'country_code')
    op.drop_column('stories', 'seo_keywords')
    op.drop_column('stories', 'og_image')
    op.drop_column('stories', 'og_description')
    op.drop_column('stories', 'og_title')
    op.drop_column('stories', 'meta_description')
