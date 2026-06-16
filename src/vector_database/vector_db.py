import logging
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.vector_database.constants import _VECTOR_STORE_DIR
from src.azure.storage_account.constants import _EMBED_MODEL
from src.azure.storage_account.storage_accounts import StorageAccount
from src.azure.storage_account.set_blob_service import blob_service_client

_EMBED_MODEL_PATH = Path("./models/multilingual-e5-base")

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


def _download_embed():
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=_EMBED_MODEL, local_dir=_EMBED_MODEL_PATH)

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        if not _EMBED_MODEL_PATH.exists():
            logger.info("[VDB] Downloading embedding model: %s", _EMBED_MODEL)
            _download_embed()
        logger.info("[VDB] Loading embedding model from %s", _EMBED_MODEL_PATH)
        _embeddings = HuggingFaceEmbeddings(model_name=str(_EMBED_MODEL_PATH))
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


def delete_all() -> None:
    global _vs
    try:
        _get_client().delete_collection(COLLECTION_NAME)
    except Exception:
        logger.debug("[VDB] Collection did not exist, skipping delete")
    _vs = None
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
