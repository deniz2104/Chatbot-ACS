import logging

from langchain_core.documents import Document

from src.ai_prompts.query_rewriter import decompose_query
from src.vector_database.constants import _CHUNKS_CHOSEN, _RERANKER_SCORE_THRESHOLD, _RERANKER_TOP_N
from src.vector_database.index import Bm25Index
from src.vector_database.reranker import Reranker

logger = logging.getLogger(__name__)

_search_index = Bm25Index()

def _question_with_user_context(question: str, user_context: str) -> str:
    return f"{question} {user_context}".strip() if user_context else question

def embed_query(text: str) -> list[float]:
    embedding_function = _search_index.get_embeddings()
    return list(embedding_function([text])[0])

def _search_by_meaning(embedding: list[float], max_results: int, hotspot_urls: set[str] | None) -> list[Document]:
    return _search_index.search_by_vector(embedding, max_results, hotspot_urls)

def _search_by_keywords(question: str, max_results: int, hotspot_urls: set[str] | None) -> list[Document]:
    return _search_index.keyword_search(question, max_results, hotspot_urls)

def _add_new_chunks(found_chunks: list[Document], collected_chunks: dict[int, Document]) -> None:
    for chunk in found_chunks:
        dedupe_key = hash(chunk.page_content)
        collected_chunks.setdefault(dedupe_key, chunk)


def _gather_hotspot_scoped_matches(
    sub_question: str,
    sub_question_embedding: list[float],
    context_sub_question: str | None,
    hotspot_urls: set[str] | None,
    collected_chunks: dict[int, Document],
) -> None:
    _add_new_chunks(
        _search_by_meaning(sub_question_embedding, _CHUNKS_CHOSEN, hotspot_urls), collected_chunks
    )
    _add_new_chunks(
        _search_by_keywords(sub_question, _CHUNKS_CHOSEN, hotspot_urls), collected_chunks
    )

    if context_sub_question:
        context_embedding = embed_query(context_sub_question)
        _add_new_chunks(
            _search_by_meaning(context_embedding, _CHUNKS_CHOSEN, hotspot_urls), collected_chunks
        )
        _add_new_chunks(
            _search_by_keywords(context_sub_question, _CHUNKS_CHOSEN, hotspot_urls),
            collected_chunks,
        )


def _gather_global_matches(
    sub_question: str,
    sub_question_embedding: list[float],
    context_sub_question: str | None,
    collected_chunks: dict[int, Document],
) -> None:
    _add_new_chunks(
        _search_by_meaning(sub_question_embedding, _CHUNKS_CHOSEN, hotspot_urls=None), collected_chunks
    )
    _add_new_chunks(
        _search_by_keywords(sub_question, _CHUNKS_CHOSEN, hotspot_urls=None), collected_chunks
    )

    if context_sub_question:
        _add_new_chunks(
            _search_by_keywords(context_sub_question, _CHUNKS_CHOSEN, hotspot_urls=None),
            collected_chunks,
        )


def _rerank_and_select_top(
    reranker_query: str,
    candidate_chunks: list[Document],
    top_n: int,
) -> list[Document]:
    reranker = Reranker.get_reranker()

    relevance_scores = reranker.predict(
        [(reranker_query, chunk.page_content) for chunk in candidate_chunks]
    )
    chunks_by_score_desc = sorted(
        zip(relevance_scores, candidate_chunks), key=lambda scored_chunk: scored_chunk[0], reverse=True
    )
    top_chunks = [
        chunk for score, chunk in chunks_by_score_desc[:top_n] if score >= _RERANKER_SCORE_THRESHOLD
    ]
    logger.debug("[VDB] Reranked %d candidates → top %d", len(candidate_chunks), len(top_chunks))
    return top_chunks


def query(
    question: str,
    top_n: int = _RERANKER_TOP_N,
    user_context: str = "",
    hotspot_urls: set[str] | None = None,
) -> list[Document]:
    logger.debug("[VDB] Query: %s", question[:80])

    sub_questions = decompose_query(question)
    if len(sub_questions) > 1:
        logger.debug("[VDB] Decomposed into %d sub-queries: %s", len(sub_questions), sub_questions)

    collected_chunks: dict[int, Document] = {}
    # Kept so the hotspot->global expansion below can reuse embeddings/context
    # instead of recomputing them.
    sub_question_data: list[tuple[str, list[float], str | None]] = []

    for sub_question in sub_questions:
        sub_question_embedding = embed_query(sub_question)
        context_sub_question = _question_with_user_context(sub_question, user_context) if user_context else None
        sub_question_data.append((sub_question, sub_question_embedding, context_sub_question))

        _gather_hotspot_scoped_matches(
            sub_question, sub_question_embedding, context_sub_question, hotspot_urls, collected_chunks
        )

    if hotspot_urls is not None:
        logger.debug(
            "[VDB] Hotspot search done (%d candidates) — expanding with global search",
            len(collected_chunks),
        )
        for sub_question, sub_question_embedding, context_sub_question in sub_question_data:
            _gather_global_matches(sub_question, sub_question_embedding, context_sub_question, collected_chunks)

    if not collected_chunks:
        logger.debug("[VDB] No candidates above threshold")
        return []

    reranker_query = _question_with_user_context(question, user_context)
    return _rerank_and_select_top(reranker_query, list(collected_chunks.values()), top_n)
