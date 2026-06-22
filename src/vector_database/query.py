import logging
from src.vector_database.constants import _CHUNKS_CHOSEN, _RERANKER_MODEL, _RERANKER_TOP_N, _SIMILARITY_THRESHOLD
from sentence_transformers import CrossEncoder
from src.vector_database.vector_db import search_all, keyword_search
from src.ai_prompts.query_rewriter import decompose_query, rewrite_query
from src.ai_prompts.hyde import generate_hypothetical_doc
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
    _get_reranker()
    logger.info("[VDB] Query system initialized")

def shutdown_query() -> None:
    global _reranker
    _reranker = None
    logger.info("[VDB] Reranker shut down")


def query(question: str, k: int = _CHUNKS_CHOSEN, top_n: int = _RERANKER_TOP_N, user_context: str = "") -> list[Document]:
    logger.debug("[VDB] Query (k=%d): %s", k, question[:80])

    sub_queries = decompose_query(rewrite_query(question))
    if len(sub_queries) > 1:
        logger.debug("[VDB] Decomposed into %d sub-queries: %s", len(sub_queries), sub_queries)

    seen: set[int] = set()
    candidates: list[Document] = []
    for sub_q in sub_queries:
        hyde_input = f"[{user_context}] {sub_q}" if user_context else sub_q
        hyde_doc = generate_hypothetical_doc(hyde_input)
        for doc, score in search_all(hyde_doc, k=k):
            if score >= _SIMILARITY_THRESHOLD:
                content_id = hash(doc.page_content)
                if content_id not in seen:
                    seen.add(content_id)
                    candidates.append(doc)

        for doc in keyword_search(question, k=k // 2):
            content_id = hash(doc.page_content)
            if content_id not in seen:
                seen.add(content_id)
                candidates.append(doc)

    if not candidates:
        logger.debug("[VDB] No candidates above threshold")
        return []

    reranker = _get_reranker()
    scores = reranker.predict([(question, doc.page_content) for doc in candidates])
    reranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)

    results = [doc for _, doc in reranked[:top_n]]
    logger.debug("[VDB] Reranked %d candidates → top %d", len(candidates), len(results))
    return results
