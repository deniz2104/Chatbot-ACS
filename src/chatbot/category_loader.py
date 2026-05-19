import logging
import threading
import torch
from pathlib import Path

logger = logging.getLogger(__name__)

_cache: dict[str, list] = {}
_lock = threading.Lock()

def _load_categories(files_store: str) -> list:
    with _lock:
        if files_store in _cache:
            return _cache[files_store]

    path = Path(files_store, "categories_encoded.pt")
    try:
        categories = torch.load(path, weights_only=False)
        with _lock:
            _cache[files_store] = categories
        logger.info("[QUERY] Loaded %d pre-encoded categories from %s", len(categories), path)
        return categories
    except FileNotFoundError:
        logger.warning("[QUERY] Failed to load %s", path)
        return []

def invalidate_categories_cache() -> None:
    with _lock:
        _cache.clear()
