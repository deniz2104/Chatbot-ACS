import logging
from src.vector_database.constants import _CHUNKS_CHOSEN, _RERANKER_MODEL, _RERANKER_TOP_N, _SIMILARITY_THRESHOLD
from sentence_transformers import CrossEncoder
from src.vector_database.vector_db import search_all
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        try:
            _reranker = CrossEncoder(_RERANKER_MODEL, max_length=512)
            logger.info("[VDB] Reranker loaded: %s", _RERANKER_MODEL)
        except Exception as e:
            logger.error("[VDB] Failed to load reranker model '%s': %s", _RERANKER_MODEL, e)
            raise RuntimeError(f"Could not load reranker model '{_RERANKER_MODEL}'") from e
    return _reranker


def initialize_query() -> None:
    """Eagerly load the reranker at startup so misconfiguration fails fast."""
    _get_reranker()


def shutdown_query() -> None:
    global _reranker
    _reranker = None
    logger.info("[VDB] Reranker shut down")


def query(question: str, k: int = _CHUNKS_CHOSEN, top_n: int = _RERANKER_TOP_N) -> list[Document]:
    logger.debug("[VDB] Query (k=%d): %s", k, question[:80])

    candidates = [
        doc
        for doc, score in search_all(question, k=k)
        if score >= _SIMILARITY_THRESHOLD
    ]

    if not candidates:
        logger.debug("[VDB] No candidates above threshold")
        return []

    reranker = _get_reranker()
    scores = reranker.predict([(question, doc.page_content) for doc in candidates])
    reranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)

    results = [doc for _, doc in reranked[:top_n]]
    logger.debug("[VDB] Reranked %d candidates → top %d", len(candidates), len(results))
    return results
