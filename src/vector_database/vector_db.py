import logging
import os
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.vector_database.constants import _CHUNKS_CHOSEN
from src.azure.kv.get_secrets_from_kv import get_chroma_host

_EMBED_MODEL_PATH = Path(os.environ.get("EMBED_MODEL_PATH", "./models/multilingual-e5-large"))
_EMBED_MODEL_HF_ID = "intfloat/multilingual-e5-large"

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents"
_CHROMA_PORT = 80

_client: ClientAPI | None = None
_embeddings = None
_vs: Chroma | None = None
_bm25_index = None
_bm25_docs: list[Document] = []
_crawl_ids: dict[str, set[str]] = {}


def _get_client() -> ClientAPI:
    global _client
    if _client is None:
        local_path = os.environ.get("CHROMA_LOCAL_PATH")
        if local_path:
            _client = chromadb.PersistentClient(path=local_path)
        else:
            _client = chromadb.HttpClient(host=get_chroma_host(), port=_CHROMA_PORT)
    return _client


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        model_name = str(_EMBED_MODEL_PATH) if _EMBED_MODEL_PATH.exists() else _EMBED_MODEL_HF_ID
        logger.info("[VDB] Loading embedding model from %s", model_name)
        _embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _get_vectorstore() -> Chroma:
    global _vs
    if _vs is None:
        _vs = Chroma(
            client=_get_client(),
            collection_name=COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _vs


def _reset_client() -> None:
    global _client, _vs
    _client = None
    _vs = None
    logger.warning("[VDB] Chroma client reset — will reconnect on next call")


def start_crawl() -> None:
    global _crawl_ids
    _crawl_ids = {}

def get_crawl_ids() -> dict[str, set[str]]:
    return _crawl_ids

def get_all_url_chunk_ids() -> dict[str, set[str]]:
    try:
        raw = _get_client().get_collection(COLLECTION_NAME).get(include=["metadatas"])
    except Exception:
        return {}
    result: dict[str, set[str]] = {}
    for chunk_id, meta in zip(raw["ids"], raw["metadatas"]):
        slug = meta.get("url_slug", "")
        result.setdefault(slug, set()).add(chunk_id)
    return result


def delete_chunks(ids: list[str]) -> None:
    if not ids:
        return
    try:
        _get_client().get_collection(COLLECTION_NAME).delete(ids=ids)
        logger.info("[VDB] Deleted %d stale chunk(s)", len(ids))
    except Exception as e:
        logger.error("[VDB] delete_chunks failed: %s", e)


def store_documents(chunks: list[Document], ids: list[str]) -> None:
    if not chunks:
        return
    try:
        _get_vectorstore().add_documents(documents=chunks, ids=ids)
    except Exception as e:
        logger.warning("[VDB] store_documents failed (%s) — resetting client and retrying", e)
        _reset_client()
        _get_vectorstore().add_documents(documents=chunks, ids=ids)
    for chunk, chunk_id in zip(chunks, ids):
        slug = chunk.metadata.get("url_slug", "")
        _crawl_ids.setdefault(slug, set()).add(chunk_id)
    logger.info("[VDB] Stored %d document(s)", len(chunks))


def search_all(query: str, k: int = _CHUNKS_CHOSEN, urls: list[str] | None = None) -> list[tuple[Document, float]]:
    chroma_filter = {"url_slug": {"$in": urls}} if urls else None
    return _get_vectorstore().similarity_search_with_relevance_scores(query, k=k, filter=chroma_filter)


def _tokenize(text: str) -> list[str]:
    import re
    return re.findall(r'\w+', text.lower())


def _get_bm25():
    global _bm25_index, _bm25_docs
    if _bm25_index is None:
        from rank_bm25 import BM25Okapi
        logger.info("[VDB] Building BM25 index...")
        raw = _get_client().get_collection(COLLECTION_NAME).get(include=["documents", "metadatas"])
        _bm25_docs = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(raw["documents"], raw["metadatas"])
        ]
        if not _bm25_docs:
            logger.warning("[VDB] BM25: collection is empty, skipping index build")
            return None
        _bm25_index = BM25Okapi([_tokenize(doc.page_content) for doc in _bm25_docs])
        logger.info("[VDB] BM25 index built over %d documents", len(_bm25_docs))
    return _bm25_index


def keyword_search(query: str, k: int = _CHUNKS_CHOSEN, urls: list[str] | None = None) -> list[tuple[Document, float]]:
    bm25 = _get_bm25()
    if bm25 is None:
        return []
    scores = bm25.get_scores(_tokenize(query))
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    url_set = set(urls) if urls else None
    return [
        (_bm25_docs[i], float(scores[i]))
        for i in top_indices
        if scores[i] > 0 and (url_set is None or _bm25_docs[i].metadata.get("url_slug") in url_set)
    ]
