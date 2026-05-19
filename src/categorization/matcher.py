import logging
from sentence_transformers import util
from src.categorization.constants import _SIMILARITY_THRESHOLD
from src.categorization.utils import _encode_matrix

logger = logging.getLogger(__name__)

def categorize(keywords: list[str], category_keywords: dict[str, list[str]]) -> str | None:
    if not keywords or not category_keywords:
        return None

    page_embs = _encode_matrix(keywords)

    best_cat, best_score = None, 0.0
    for category, kws in category_keywords.items():
        cat_embs = _encode_matrix(kws)
        score = float(util.cos_sim(page_embs, cat_embs).max())
        if score > best_score:
            best_cat, best_score = category, score

    if best_score >= _SIMILARITY_THRESHOLD:
        logger.debug("[CATEGORIZE] '%s' (score=%.3f)", best_cat, best_score)
        return best_cat

    logger.debug("[CATEGORIZE] No category matched (best=%.3f)", best_score)
    return None
