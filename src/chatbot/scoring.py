from sentence_transformers import util

# Category embeddings capture broad topics, so a lower threshold avoids
# blocking categories whose individual URLs are highly relevant.
_CATEGORY_THRESHOLD = 0.50
_URL_THRESHOLD = 0.60
_TOP_CATEGORIES = 5


def _score_and_filter(query_emb, items: list, threshold: float) -> list:
    result = []
    for emb, payload in items:
        sim = util.cos_sim(query_emb, emb)
        score = float(sim.max(dim=1).values.mean())
        if score >= threshold:
            result.append((score, payload))
    return result


def _score_categories(query_emb, categories: list) -> list:
    items = [(cat_emb, url_entries) for cat_emb, url_entries in categories]
    return sorted(
        _score_and_filter(query_emb, items, _CATEGORY_THRESHOLD),
        reverse=True,
    )[:_TOP_CATEGORIES]


def _score_urls(query_emb, url_entries: list) -> list:
    items = [(url_emb, url) for url, url_emb in url_entries]
    return _score_and_filter(query_emb, items, _URL_THRESHOLD)
