import json
import os

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from src.spider.items import DocumentItem
from src.spider.utils import normalize_url

class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        href_field = "document_href" if isinstance(item, DocumentItem) else "href"
        href = adapter.get(href_field)
        if not href:
            raise DropItem(f"Missing {href_field}")
        adapter[href_field] = normalize_url(href)
        return item

## de schimbat pe redis
class DeduplicationPipeline:
    def __init__(self):
        self.seen_hrefs: set[str] = set()

    def process_item(self, item, _spider):
        adapter = ItemAdapter(item)
        href = adapter["document_href"] if isinstance(item, DocumentItem) else adapter["href"]
        if href in self.seen_hrefs:
            raise DropItem(f"Duplicate link: {href}")
        self.seen_hrefs.add(href)
        return item

## de verificat si schimbat pe redis
class MergePipeline:
    def __init__(self):
        self.old_pages: dict[str, dict] = {}
        self.new_pages: dict[str, dict] = {}
        self.old_docs: dict[str, dict] = {}
        self.new_docs: dict[str, dict] = {}

    def _load(self, path: str, key: str) -> dict[str, dict]:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return {e[key]: e for e in json.load(f) if e.get(key)}
        return {}

    def _write(self, path: str, old: dict, new: dict, spider, label: str):
        merged = {**old, **new}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)
        spider.logger.info(
            f"Wrote {len(merged)} {label} "
            f"({len(new)} crawled, {len(merged) - len(new)} preserved from previous)"
        )

    def open_spider(self, spider):
        self.old_pages = self._load(spider.settings.get("OUTPUT_PATH"), "href")
        self.old_docs = self._load(spider.settings.get("DOCUMENTS_OUTPUT_PATH"), "document_href")
        spider.logger.info(f"Loaded {len(self.old_pages)} existing pages, {len(self.old_docs)} existing documents")

    def _resolve(self, old_entry: dict | None, href: str, new_hash: str | None,
                 hash_field: str, label: str, spider) -> bool:
        if old_entry and old_entry.get(hash_field) == new_hash:
            spider.logger.debug(f"Unchanged {label}: {href}")
            return True
        spider.logger.info(f"{'Updated' if old_entry else 'New'} {label}: {href}")
        return False

    def _extract(self, adapter: ItemAdapter, store: dict, href_field: str, hash_field: str,
                 utc_field: str, label: str, spider) -> tuple[str, str | None, dict | None, bool, str | None]:
        href = adapter[href_field]
        new_hash = adapter.get(hash_field)
        old_entry = store.get(href)
        unchanged = self._resolve(old_entry, href, new_hash, hash_field, label, spider)
        utc = old_entry.get(utc_field) if (unchanged and old_entry) else adapter.get(utc_field)
        return href, new_hash, old_entry, unchanged, utc

    def _merge_document(self, adapter: ItemAdapter, spider) -> None:
        href, new_hash, _, _, utc = self._extract(
            adapter, self.old_docs, "document_href", "document_hash", "document_utc", "document", spider
        )
        self.new_docs[href] = {"document_href": href, "document_utc": utc, "document_hash": new_hash}

    def _merge_page(self, adapter: ItemAdapter, spider) -> None:
        href, new_hash, old_entry, unchanged, utc = self._extract(
            adapter, self.old_pages, "href", "hash", "utc", "link", spider
        )
        content = old_entry.get("content", "") if (unchanged and old_entry) else adapter.get("content", "")
        self.new_pages[href] = {
            "href": href,
            "href_text": adapter.get("href_text", ""),
            "content": content,
            "utc": utc,
            "hash": new_hash,
        }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if isinstance(item, DocumentItem):
            self._merge_document(adapter, spider)
        else:
            self._merge_page(adapter, spider)
        return item

    def close_spider(self, spider):
        self._write(spider.settings.get("OUTPUT_PATH"), self.old_pages, self.new_pages, spider, "entries")
        self._write(spider.settings.get("DOCUMENTS_OUTPUT_PATH"), self.old_docs, self.new_docs, spider, "documents")
