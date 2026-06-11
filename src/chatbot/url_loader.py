import json
from pathlib import Path
from typing import Optional
from src.files_store.init_files import get_chatbot_file_store

_loaded_urls_cache: set[str] = set()

def _load_crawled_urls(files_store: Optional[str] = None) -> set[str]:
    if files_store is None:
        files_store = get_chatbot_file_store()

    if _loaded_urls_cache:
        return set(_loaded_urls_cache)

    path = Path(files_store, "chatbot_output.json")
    try:
        urls = set(json.loads(path.read_text(encoding="utf-8")))
        _loaded_urls_cache.update(urls)
        return urls
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def invalidate_urls_cache() -> None:
    _loaded_urls_cache.clear()
