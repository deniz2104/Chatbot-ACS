import logging
from src.vector_database.constants import CHUNKS_CHOSEN, RERANKER_TOP_N, SIMILARITY_THRESHOLD, RERANKER_MODEL
from sentence_transformers import CrossEncoder
from src.vector_database.vector_db import search_all
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        try:
            _reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
            logger.info("[VDB] Reranker loaded: %s", RERANKER_MODEL)
        except Exception as e:
            logger.error("[VDB] Failed to load reranker model '%s': %s", RERANKER_MODEL, e)
            raise RuntimeError(f"Could not load reranker model '{RERANKER_MODEL}'") from e
    return _reranker


def initialize_query() -> None:
    """Eagerly load the reranker at startup so misconfiguration fails fast."""
    _get_reranker()


def shutdown_query() -> None:
    global _reranker
    _reranker = None
    logger.info("[VDB] Reranker shut down")


def query(question: str, k: int = CHUNKS_CHOSEN, top_n: int = RERANKER_TOP_N) -> list[Document]:
    logger.debug("[VDB] Query (k=%d): %s", k, question[:80])

    candidates = [
        doc
        for doc, score in search_all(question, k=k)
        if score >= SIMILARITY_THRESHOLD
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
