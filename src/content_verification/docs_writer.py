import os
import shutil
from urllib.parse import urlparse

from src.spider.utils import get_urls

class DocsWriter:
    def __init__(self):
        os.makedirs("src/content_verification/docs", exist_ok=True)
        self._urls = get_urls()
        self._ensure_per_website_files()
        self._buffers = {url: [] for url in self._urls}

    def _ensure_per_website_files(self):
        for url in self._urls:
            filename = f"src/content_verification/docs/{url.split('/')[2]}.txt"
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8"):
                    pass

    def add_content(self, content: str, url: str):
        domain = "https://" + urlparse(url).hostname
        if domain not in self._buffers:
            return
        separator = "=" * 50
        entry = f"{url}\n{content}\n{separator}\n"
        self._buffers[domain].append(entry)

    def flush_buffers(self):
        for url, entries in self._buffers.items():
            if entries:
                filename = f"src/content_verification/docs/{url.split('/')[2]}.txt"
                with open(filename, "a", encoding="utf-8") as f:
                    f.writelines(entries)

    def delete_docs_folder(self):
        directory = os.path.join("src/content_verification/docs")
        shutil.rmtree(directory, ignore_errors=True)