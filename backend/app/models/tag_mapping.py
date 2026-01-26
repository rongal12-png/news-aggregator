from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index

from .base import Base


class TagMapping(Base):
    """Tag normalization mapping table.

    Maps raw tags (e.g., 'crypto', 'btc') to normalized forms (e.g., 'cryptocurrency', 'bitcoin').
    Supports multiple languages with language-specific mappings.
    """
    __tablename__ = "tag_mappings"

    id = Column(Integer, primary_key=True, index=True)
    raw_tag = Column(String(100), nullable=False)
    normalized_tag = Column(String(100), nullable=False)
    language = Column(String(10), nullable=False, default="en")
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    __table_args__ = (
        UniqueConstraint("raw_tag", "language", name="uq_tag_mapping_raw_lang"),
        Index("idx_tag_mappings_raw", "raw_tag"),
        Index("idx_tag_mappings_normalized", "normalized_tag"),
    )

    def __repr__(self):
        return f"<TagMapping '{self.raw_tag}' -> '{self.normalized_tag}' ({self.language})>"


class ClusterSimilarity(Base):
    """Tracks similarity between story clusters for potential merging.

    Used by fuzzy clustering to identify stories that might be about the same topic
    but weren't matched by exact normalized_key matching.
    """
    __tablename__ = "cluster_similarities"

    id = Column(Integer, primary_key=True, index=True)
    story_id_1 = Column(Integer, nullable=False, index=True)
    story_id_2 = Column(Integer, nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    merged = Column(String(10), nullable=False, default="false")
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    __table_args__ = (
        UniqueConstraint("story_id_1", "story_id_2", name="uq_cluster_similarity_pair"),
        Index("idx_cluster_sim_score", "similarity_score"),
    )

    def __repr__(self):
        return f"<ClusterSimilarity {self.story_id_1}<->{self.story_id_2} score={self.similarity_score}>"
