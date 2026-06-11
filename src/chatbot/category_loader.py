import logging
import torch
from pathlib import Path
from typing import Optional
from src.files_store.init_files import get_general_file_store

logger = logging.getLogger(__name__)

_cache: dict[str, list] = {}

def _load_categories(files_store: Optional[str] = None) -> list:
    if files_store is None:
        files_store = get_general_file_store()

    if files_store in _cache:
        return _cache[files_store]

    path = Path(files_store, "categories_encoded.pt")
    try:
        categories = torch.load(path, weights_only=False)
        _cache[files_store] = categories
        logger.info("[QUERY] Loaded %d pre-encoded categories from %s", len(categories), path)
        return categories
    except FileNotFoundError:
        logger.warning("[QUERY] Failed to load %s", path)
        return []

def invalidate_categories_cache() -> None:
    _cache.clear()
