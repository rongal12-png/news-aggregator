"""add story category

Revision ID: 002
Revises: 001
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category column with default value
    op.add_column('stories', sa.Column('category', sa.String(50), nullable=False, server_default='general'))

    # Create index
    op.create_index('idx_stories_category', 'stories', ['category'])

    # Update existing stories based on their articles' source categories
    op.execute("""
        UPDATE stories SET category = (
            SELECT COALESCE(s.category, 'general')
            FROM articles a
            JOIN sources s ON a.source_id = s.id
            WHERE a.story_id = stories.id
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM articles WHERE articles.story_id = stories.id
        )
    """)


def downgrade() -> None:
    op.drop_index('idx_stories_category', table_name='stories')
    op.drop_column('stories', 'category')
