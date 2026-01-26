"""Add cluster_similarities table for fuzzy matching

Revision ID: 005
Revises: 004
Create Date: 2024-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cluster_similarities table for tracking similar stories
    op.create_table(
        'cluster_similarities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id_1', sa.Integer(), nullable=False),
        sa.Column('story_id_2', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('merged', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['story_id_1'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['story_id_2'], ['stories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id_1', 'story_id_2', name='uq_cluster_similarity_pair')
    )
    op.create_index('idx_cluster_sim_score', 'cluster_similarities', ['similarity_score'])
    op.create_index('idx_cluster_sim_story1', 'cluster_similarities', ['story_id_1'])
    op.create_index('idx_cluster_sim_story2', 'cluster_similarities', ['story_id_2'])
    op.create_index('idx_cluster_sim_merged', 'cluster_similarities', ['merged'])


def downgrade() -> None:
    op.drop_index('idx_cluster_sim_merged', table_name='cluster_similarities')
    op.drop_index('idx_cluster_sim_story2', table_name='cluster_similarities')
    op.drop_index('idx_cluster_sim_story1', table_name='cluster_similarities')
    op.drop_index('idx_cluster_sim_score', table_name='cluster_similarities')
    op.drop_table('cluster_similarities')
