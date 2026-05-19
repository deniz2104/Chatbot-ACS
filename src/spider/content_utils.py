import logging
import re
import unicodedata

from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    canon = canonicalize_url(url)
    if not canon:
        return canon
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

def normalize_markdown(text: str) -> str:
    if not text:
        return ""
    
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r" +$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^(#{1,6})\s*(.+)$", r"\1 \2", text, flags=re.MULTILINE)
    return text.strip() + "\n"