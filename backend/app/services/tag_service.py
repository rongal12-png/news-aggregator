from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models import TagMapping


class TagService:
    """Service for normalizing and managing tags across languages."""

    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, str] = {}

    def normalize_tag(self, raw_tag: str, language: str = 'en') -> str:
        """
        Normalize a tag using the mappings table.

        Args:
            raw_tag: The original tag to normalize
            language: The language context (defaults to 'en')

        Returns:
            Normalized tag string
        """
        cache_key = f"{raw_tag.lower()}:{language}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        mapping = (
            self.db.query(TagMapping)
            .filter(
                TagMapping.raw_tag == raw_tag.lower(),
                TagMapping.language == language
            )
            .first()
        )

        normalized = mapping.normalized_tag if mapping else raw_tag.lower()
        self._cache[cache_key] = normalized
        return normalized

    def normalize_tags(self, tags: List[str], language: str = 'en') -> List[str]:
        """
        Normalize a list of tags, removing duplicates while preserving order.

        Args:
            tags: List of raw tags
            language: Language context

        Returns:
            List of normalized tags without duplicates
        """
        normalized = [self.normalize_tag(t, language) for t in tags]
        # Preserve order, remove duplicates
        return list(dict.fromkeys(normalized))

    def add_mapping(
        self,
        raw_tag: str,
        normalized_tag: str,
        language: str = 'en',
        confidence: float = 1.0
    ) -> TagMapping:
        """
        Add or update a tag mapping.

        Args:
            raw_tag: The raw tag to map from
            normalized_tag: The normalized form to map to
            language: Language for this mapping
            confidence: Confidence score (0-1)

        Returns:
            Created or updated TagMapping
        """
        existing = (
            self.db.query(TagMapping)
            .filter(
                TagMapping.raw_tag == raw_tag.lower(),
                TagMapping.language == language
            )
            .first()
        )

        if existing:
            existing.normalized_tag = normalized_tag
            existing.confidence = confidence
            mapping = existing
        else:
            mapping = TagMapping(
                raw_tag=raw_tag.lower(),
                normalized_tag=normalized_tag,
                language=language,
                confidence=confidence
            )
            self.db.add(mapping)

        self.db.commit()

        # Clear cache for this tag
        cache_key = f"{raw_tag.lower()}:{language}"
        if cache_key in self._cache:
            del self._cache[cache_key]

        return mapping

    def get_all_mappings(self, language: Optional[str] = None) -> List[TagMapping]:
        """
        Get all tag mappings, optionally filtered by language.

        Args:
            language: Optional language filter

        Returns:
            List of TagMapping objects
        """
        query = self.db.query(TagMapping)
        if language:
            query = query.filter(TagMapping.language == language)
        return query.order_by(TagMapping.normalized_tag).all()

    def get_synonyms(self, normalized_tag: str, language: str = 'en') -> List[str]:
        """
        Get all raw tags that map to a normalized tag.

        Args:
            normalized_tag: The normalized tag to search for
            language: Language context

        Returns:
            List of raw tags (synonyms)
        """
        mappings = (
            self.db.query(TagMapping)
            .filter(
                TagMapping.normalized_tag == normalized_tag,
                TagMapping.language == language
            )
            .all()
        )
        return [m.raw_tag for m in mappings]

    def clear_cache(self):
        """Clear the in-memory tag mapping cache."""
        self._cache.clear()
