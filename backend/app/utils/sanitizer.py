import bleach
import re


ALLOWED_TAGS = []  # Strip all HTML tags
ALLOWED_ATTRIBUTES = {}


def sanitize_html(text: str, max_length: int | None = None) -> str:
    """
    Sanitize HTML content and optionally truncate.
    """
    if not text:
        return ""

    # Strip HTML tags
    clean = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

    # Normalize whitespace
    clean = re.sub(r"\s+", " ", clean)
    clean = clean.strip()

    # Truncate if needed
    if max_length and len(clean) > max_length:
        clean = clean[:max_length - 3] + "..."

    return clean
