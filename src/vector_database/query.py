import logging
import os
from pathlib import Path

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from src.ai_prompts.hyde import generate_hypothetical_doc
from src.ai_prompts.query_rewriter import decompose_query
from src.vector_database.constants import _CHUNKS_CHOSEN, _RERANKER_MODEL, _RERANKER_SCORE_THRESHOLD, _RERANKER_TOP_N, _SIMILARITY_THRESHOLD
from src.vector_database.vector_db import search_all, keyword_search

_RERANKER_PATH = Path(os.environ.get("RERANKER_MODEL_PATH", "./models/bge-reranker-v2-m3"))

logger = logging.getLogger(__name__)

_reranker = None

def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        model = str(_RERANKER_PATH) if _RERANKER_PATH.exists() else _RERANKER_MODEL
        try:
            _reranker = CrossEncoder(model, max_length=512)
            logger.info("[VDB] Reranker loaded from: %s", model)
        except Exception as e:
            logger.error("[VDB] Failed to load reranker '%s': %s", model, e)
            raise RuntimeError(f"Could not load reranker '{model}'") from e
    return _reranker

def initialize_query() -> None:
    _get_reranker()
    logger.info("[VDB] Query system initialized")

def _rag_search_helper(
    question: str,
    k: int = _CHUNKS_CHOSEN,
    urls: list[str] | None = None,
    kw_search : bool = True
) -> dict[int, list[Document]]:
    
    result: dict[int, list[Document]] = {}
    function_call = keyword_search if kw_search else search_all
    
    for doc, score in function_call(question, k, urls):
        if kw_search or score >= _SIMILARITY_THRESHOLD:
            content_id = hash(doc.page_content)
            result.setdefault(content_id, []).append(doc)
    return result

def _merge_into(
    batch: dict[int, list[Document]],
    seen: set[int],
    candidates: list[Document],
) -> None:
    
    for content_id, docs in batch.items():
        if content_id not in seen:
            seen.add(content_id)
            candidates.append(docs[0])

def query(
    question: str,
    top_n: int = _RERANKER_TOP_N,
    user_context: str = "",
    urls: list[str] | None = None,
) -> list[Document]:
    
    logger.debug("[VDB] Query: %s", question[:80])

    sub_queries = decompose_query(question)
    if len(sub_queries) > 1:
        logger.debug("[VDB] Decomposed into %d sub-queries: %s", len(sub_queries), sub_queries)

    seen: set[int] = set()
    candidates: list[Document] = []
    sub_queries_with_hyde: list[tuple[str, str]] = []

    for sub_q in sub_queries:
        hyde_input = f"[{user_context}] {sub_q}" if user_context else sub_q
        hyde_doc = generate_hypothetical_doc(hyde_input)
        sub_queries_with_hyde.append((sub_q, hyde_doc))

        _merge_into(_rag_search_helper(hyde_doc, urls=urls, kw_search=False), seen, candidates)
        _merge_into(_rag_search_helper(sub_q, k=_CHUNKS_CHOSEN // 2, urls=urls, kw_search=False), seen, candidates)
        _merge_into(_rag_search_helper(sub_q, k=_CHUNKS_CHOSEN // 2, urls=urls), seen, candidates)

    if urls is not None:
        logger.debug("[VDB] Hotspot search done (%d candidates) — expanding with global search", len(candidates))
        for sub_q, hyde_doc in sub_queries_with_hyde:
            _merge_into(_rag_search_helper(hyde_doc, urls=None, kw_search=False), seen, candidates)
            _merge_into(_rag_search_helper(sub_q, k=_CHUNKS_CHOSEN // 2, urls=None, kw_search=False), seen, candidates)
            _merge_into(_rag_search_helper(sub_q, k=_CHUNKS_CHOSEN // 2, urls=None), seen, candidates)

    if not candidates:
        logger.debug("[VDB] No candidates above threshold")
        return []

    reranker = _get_reranker()
    scores = reranker.predict([(question, doc.page_content) for doc in candidates])
    reranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    results = [doc for score, doc in reranked[:top_n] if score >= _RERANKER_SCORE_THRESHOLD]
    logger.debug("[VDB] Reranked %d candidates → top %d", len(candidates), len(results))
    return results
