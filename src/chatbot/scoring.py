from sentence_transformers import util

_QUERY_THRESHOLD = 0.65
_TOP_CATEGORIES = 3

def _score_and_filter(query_emb, items: list) -> list:
    result = []
    for emb, payload in items:
        score = float(util.cos_sim(query_emb, emb).max())
        if score >= _QUERY_THRESHOLD:
            result.append((score, payload))
    return result

def _score_categories(query_emb, categories: list) -> list:
    items = [(cat_emb, url_entries) for cat_emb, url_entries in categories]
    return sorted(_score_and_filter(query_emb, items), reverse=True)[:_TOP_CATEGORIES]

def _score_urls(query_emb, url_entries: list) -> list:
    items = [(url_emb, url) for url, url_emb in url_entries]
    return _score_and_filter(query_emb, items)
