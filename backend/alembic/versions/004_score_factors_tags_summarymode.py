"""Add score_factors, tag_mappings, and summary mode

Revision ID: 004
Revises: 003
Create Date: 2024-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add score_factors JSONB column to stories table
    op.add_column(
        'stories',
        sa.Column('score_factors', postgresql.JSONB(astext_type=sa.Text()),
                  server_default='{}', nullable=False)
    )

    # Add mode column to story_summaries table
    op.add_column(
        'story_summaries',
        sa.Column('mode', sa.String(length=20), server_default='standard', nullable=False)
    )

    # Update unique constraint to include mode
    # First drop the old constraint
    op.drop_constraint('uq_summary_story_language', 'story_summaries', type_='unique')
    # Create new composite unique constraint
    op.create_unique_constraint(
        'uq_summary_story_language_mode',
        'story_summaries',
        ['story_id', 'language', 'mode']
    )

    # Create tag_mappings table for tag normalization
    op.create_table(
        'tag_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_tag', sa.String(length=100), nullable=False),
        sa.Column('normalized_tag', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_tag', 'language', name='uq_tag_mapping_raw_lang')
    )
    op.create_index('idx_tag_mappings_raw', 'tag_mappings', ['raw_tag'])
    op.create_index('idx_tag_mappings_normalized', 'tag_mappings', ['normalized_tag'])

    # Insert initial tag mappings for common synonyms
    op.execute("""
        INSERT INTO tag_mappings (raw_tag, normalized_tag, language) VALUES
        ('crypto', 'cryptocurrency', 'en'),
        ('btc', 'bitcoin', 'en'),
        ('eth', 'ethereum', 'en'),
        ('ai', 'artificial-intelligence', 'en'),
        ('ml', 'machine-learning', 'en'),
        ('dl', 'deep-learning', 'en'),
        ('llm', 'large-language-model', 'en'),
        ('gpt', 'large-language-model', 'en'),
        ('nft', 'nft', 'en'),
        ('defi', 'decentralized-finance', 'en'),
        ('web3', 'web3', 'en'),
        ('ipo', 'initial-public-offering', 'en'),
        ('sec', 'securities-exchange-commission', 'en'),
        ('fed', 'federal-reserve', 'en'),
        ('gdp', 'gross-domestic-product', 'en'),
        ('ev', 'electric-vehicle', 'en'),
        ('vr', 'virtual-reality', 'en'),
        ('ar', 'augmented-reality', 'en'),
        ('iot', 'internet-of-things', 'en'),
        ('saas', 'software-as-a-service', 'en')
    """)

    # Hebrew tag mappings
    op.execute("""
        INSERT INTO tag_mappings (raw_tag, normalized_tag, language) VALUES
        ('קריפטו', 'cryptocurrency', 'he'),
        ('ביטקוין', 'bitcoin', 'he'),
        ('בינה מלאכותית', 'artificial-intelligence', 'he'),
        ('למידת מכונה', 'machine-learning', 'he'),
        ('בלוקצ''יין', 'blockchain', 'he'),
        ('סטארטאפ', 'startup', 'he'),
        ('הייטק', 'tech', 'he'),
        ('כלכלה', 'economy', 'he'),
        ('פיננסים', 'finance', 'he'),
        ('בורסה', 'stock-market', 'he')
    """)


def downgrade() -> None:
    # Drop tag_mappings table
    op.drop_index('idx_tag_mappings_normalized', table_name='tag_mappings')
    op.drop_index('idx_tag_mappings_raw', table_name='tag_mappings')
    op.drop_table('tag_mappings')

    # Restore original unique constraint
    op.drop_constraint('uq_summary_story_language_mode', 'story_summaries', type_='unique')
    op.create_unique_constraint(
        'uq_summary_story_language',
        'story_summaries',
        ['story_id', 'language']
    )

    # Remove mode column from story_summaries
    op.drop_column('story_summaries', 'mode')

    # Remove score_factors from stories
    op.drop_column('stories', 'score_factors')
