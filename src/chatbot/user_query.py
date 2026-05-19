import logging

from src.ai_prompts.keywords_extractor import extract_keywords
from src.categorization.utils import _encode_matrix
from src.chatbot.category_loader import _load_categories
from src.chatbot.scoring import _score_categories, _score_urls

logger = logging.getLogger(__name__)

def resolve_urls(query: str, files_store: str) -> list[str]:
    query_keywords = extract_keywords(query, tokens=256)
    if not query_keywords:
        logger.warning("[QUERY] No keywords extracted from query")
        return []

    categories = _load_categories(files_store)
    if not categories:
        logger.warning("[QUERY] No crawl data found in %s", files_store)
        return []

    query_emb = _encode_matrix(query_keywords)
    top_categories = _score_categories(query_emb, categories)

    seen: set[str] = set()
    urls: list[str] = []
    for _, url_entries in top_categories:
        for _, url in _score_urls(query_emb, url_entries):
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls
