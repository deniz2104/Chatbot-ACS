import logging
from src.categorization.utils import _encode_matrix

logger = logging.getLogger(__name__)

def load_and_encode_categories(general_entries: dict) -> list[tuple]:
    categories = []
    for domain_data in general_entries.values():
        for cat_data in domain_data.values():
            predefined = cat_data.get("predefined_keywords", [])
            urls = cat_data.get("urls", [])
            if not predefined or not urls:
                logger.warning(
                    "[ENCODE] Skipping category — predefined_keywords=%d, urls=%d",
                    len(predefined),
                    len(urls),
                )
                continue
            cat_emb = _encode_matrix(predefined)
            url_entries = []
            for entry in urls:
                kws = entry.get("keywords", [])
                if not kws:
                    logger.debug("[ENCODE] Skipping URL %s — no keywords", entry.get("url", "?"))
                    continue
                url_entries.append((entry["url"], _encode_matrix(kws)))
            if url_entries:
                categories.append((cat_emb, url_entries))
            else:
                logger.warning("[ENCODE] Category dropped — all URLs had empty keywords")

    return categories