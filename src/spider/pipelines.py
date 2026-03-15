import json
import os

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from src.spider.utils import normalize_url

class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        href = adapter.get("href")
        if not href:
            raise DropItem("Missing href")
        
        adapter["href"] = normalize_url(href)
        return item
    
## de schimbat pe redis
class DeduplicationPipeline:
    def __init__(self):
        self.seen_hrefs: set[str] = set()

    def process_item(self, item, spider):
        href = ItemAdapter(item)["href"]
        if href in self.seen_hrefs:
            raise DropItem(f"Duplicate link: {href}")
        self.seen_hrefs.add(href)
        return item


## de verificat si schimbat pe redis
class MergePipeline:
    def __init__(self):
        self.old_data: dict[str, dict] = {}
        self.new_data: dict[str, dict] = {}

    def open_spider(self, spider):
        output_path = spider.settings.get("OUTPUT_PATH", "src/spider/output.json")
        if os.path.isfile(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                for entry in json.load(f):
                    href = entry.get("href")
                    if href:
                        self.old_data[href] = entry
            spider.logger.info(f"Loaded {len(self.old_data)} existing entries from {output_path}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        href = adapter["href"]
        new_hash = adapter.get("hash")

        old_entry = self.old_data.get(href)
        utc = adapter.get("utc")

        if old_entry and old_entry.get("hash") == new_hash:
            utc = old_entry.get("utc", utc)
            content = old_entry.get("content", "")
            spider.logger.debug(f"Unchanged link: {href}")
        else:
            content = adapter.get("content", "")
            spider.logger.info(f"{'Updated' if old_entry else 'New'} link: {href}")

        self.new_data[href] = {
            "href": href,
            "href_text": adapter.get("href_text", ""),
            "content": content,
            "source": adapter.get("source", ""),
            "utc": utc,
            "hash": new_hash,
        }
        return item

    def close_spider(self, spider):
        merged = dict(self.old_data)
        merged.update(self.new_data)

        output_path = spider.settings.get("OUTPUT_PATH", "src/spider/output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)

        spider.logger.info(
            f"Wrote {len(merged)} entries "
            f"({len(self.new_data)} crawled, {len(merged) - len(self.new_data)} preserved from previous)"
        )
