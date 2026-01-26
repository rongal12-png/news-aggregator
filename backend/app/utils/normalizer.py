import re
import hashlib
from urllib.parse import urlparse, urlunparse


def normalize_title(title: str) -> str:
    """
    Normalize a title for clustering purposes.
    Creates a key that groups similar articles together.
    More aggressive normalization for better deduplication.
    """
    if not title:
        return ""

    # Convert to lowercase
    text = title.lower()

    # Remove common prefixes like "Breaking:", "Update:", etc.
    prefixes = [
        r"^breaking:\s*",
        r"^update:\s*",
        r"^exclusive:\s*",
        r"^report:\s*",
        r"^analysis:\s*",
        r"^opinion:\s*",
        r"^review:\s*",
        r"^watch:\s*",
        r"^live:\s*",
        r"^video:\s*",
        r"^podcast:\s*",
    ]
    for prefix in prefixes:
        text = re.sub(prefix, "", text, flags=re.IGNORECASE)

    # Remove source attributions like "- BBC", "| Reuters"
    text = re.sub(r"\s*[-|]\s*[A-Za-z]+\s*$", "", text)

    # Remove special characters and extra whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # Remove common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "again", "further",
        "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "and", "but", "if", "or",
        "because", "until", "while", "about", "against", "this",
        "that", "these", "those", "its", "it", "says", "said",
        "new", "now", "get", "got", "make", "made", "take", "took",
        "come", "came", "go", "went", "know", "knew", "think", "thought",
        "see", "saw", "want", "wanted", "use", "used", "find", "found",
        "give", "gave", "tell", "told", "work", "worked", "seem", "seemed",
        "feel", "felt", "try", "tried", "leave", "left", "call", "called",
        "first", "last", "long", "great", "little", "own", "old", "right",
        "big", "high", "different", "small", "large", "next", "early",
        "young", "important", "public", "bad", "good", "best", "worst",
    }

    words = text.split()
    # Keep words that are not stop words and have at least 3 chars
    words = [w for w in words if w not in stop_words and len(w) > 2]

    # Take first 6 significant words for the key (more strict clustering)
    key_words = words[:6]

    return " ".join(sorted(key_words))


def generate_url_hash(url: str) -> str:
    """
    Generate a SHA256 hash of a normalized URL for deduplication.
    """
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()


def normalize_url(url: str) -> str:
    """
    Normalize a URL to handle duplicates with different query params.
    """
    if not url:
        return ""

    parsed = urlparse(url)

    # Remove common tracking parameters
    tracking_params = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid",
    }

    # Rebuild URL without tracking params
    # Keep only the scheme, netloc, and path
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        "",  # params
        "",  # query - removed for simplicity
        ""   # fragment
    ))

    return normalized
