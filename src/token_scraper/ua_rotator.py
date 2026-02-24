from datetime import datetime
import os
from zoneinfo import ZoneInfo
import json

from src.token_scraper.header_builder import BrowserHeader

def make_docs_dir_if_not_exists() -> None:
    docs_path = "src/token_scraper/docs"
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

def create_browser_header():
    pass

def save_headers_to_json(headers: list[BrowserHeader], output_file: str = "src/token_scraper/docs/browser_headers.json") -> None:
    make_docs_dir_if_not_exists()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2, ensure_ascii=False)

def load_headers_from_json(path: str = "src/token_scraper/docs/browser_headers.json") -> list[BrowserHeader]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
