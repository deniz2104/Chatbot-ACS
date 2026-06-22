import logging
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.vector_database.constants import _VECTOR_STORE_DIR, _EMBED_MODEL

_EMBED_MODEL_PATH = Path("./models/multilingual-e5-large")

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents"

_client: ClientAPI | None = None
_embeddings = None
_vs: Chroma | None = None


def _get_client() -> ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=_VECTOR_STORE_DIR,
            settings=Settings(allow_reset=True),
        )
    return _client


_DOWNLOAD_IGNORE = [
    "pytorch_model.bin", "flax_model*", "tf_model*", "rust_model*",
    "*.msgpack", "onnx/*", "openvino/*", "*.yaml",
]

def _download_embed():
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=_EMBED_MODEL, local_dir=_EMBED_MODEL_PATH, ignore_patterns=_DOWNLOAD_IGNORE)

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        if not _EMBED_MODEL_PATH.exists():
            logger.info("[VDB] Downloading embedding model: %s", _EMBED_MODEL)
            _download_embed()
        logger.info("[VDB] Loading embedding model from %s", _EMBED_MODEL_PATH)
        _embeddings = HuggingFaceEmbeddings(
            model_name=str(_EMBED_MODEL_PATH),
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


def store_documents(chunks: list[Document], ids: list[str]) -> None:
    if not chunks:
        return
    _get_vectorstore().add_documents(documents=chunks, ids=ids)
    logger.info("[VDB] Stored %d document(s)", len(chunks))


def search_all(query: str, k: int = 20, urls: list[str] | None = None) -> list[tuple[Document, float]]:
    chroma_filter = {"url_slug": {"$in": urls}} if urls else None
    return _get_vectorstore().similarity_search_with_relevance_scores(query, k=k, filter=chroma_filter)


_bm25_index = None
_bm25_docs: list[Document] = []


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
        _bm25_index = BM25Okapi([_tokenize(doc.page_content) for doc in _bm25_docs])
        logger.info("[VDB] BM25 index built over %d documents", len(_bm25_docs))
    return _bm25_index


def keyword_search(query: str, k: int = 20) -> list[Document]:
    """BM25 retrieval — handles IDF natively so common words are down-weighted automatically."""
    bm25 = _get_bm25()
    scores = bm25.get_scores(_tokenize(query))
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [_bm25_docs[i] for i in top_indices if scores[i] > 0]


def delete_all() -> None:
    global _vs, _bm25_index, _bm25_docs
    try:
        _get_client().delete_collection(COLLECTION_NAME)
    except Exception:
        logger.debug("[VDB] Collection did not exist, skipping delete")
    _vs = None
    _bm25_index = None
    _bm25_docs = []
    logger.info("[VDB] Collection deleted")


def shutdown_vector_db() -> None:
    global _client, _embeddings, _vs
    _vs = None
    _embeddings = None
    if _client is not None:
        try:
            _client._system.stop()
        except Exception:
            pass
        _client = None
    logger.info("[VDB] Vector DB shut down")
