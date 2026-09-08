import logging
import re
import unicodedata

from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str | None:
    canon = canonicalize_url(url) if url else None

    if canon:
        if canon.startswith("http://"):
            canon = "https://" + canon[7:]
        canon = canon.replace("://www.", "://", 1)

    return canon

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text