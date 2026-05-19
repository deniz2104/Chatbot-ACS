import json
import threading
from pathlib import Path

_loaded_urls_cache: set[str] = set()
_lock = threading.Lock()

def _load_crawled_urls(files_store: str) -> set[str]:
    with _lock:
        if _loaded_urls_cache:
            return set(_loaded_urls_cache)

    path = Path(files_store, "chatbot_output.json")
    try:
        urls = set(json.loads(path.read_text(encoding="utf-8")))
        with _lock:
            _loaded_urls_cache.update(urls)
        return urls
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def invalidate_urls_cache() -> None:
    with _lock:
        _loaded_urls_cache.clear()
