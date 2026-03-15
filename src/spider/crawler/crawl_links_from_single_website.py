import re

from hashlib import sha256
from scrapy import Spider
from scrapy.http import Response, HtmlResponse
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from src.spider.items import PageItem
from src.spider.constants import EXTENSIONS, IGNORED_HREF_PREFIXES, PAGINATION_PATTERN

from src.spider.utils import extract_content, normalize_url
from datetime import datetime, timezone


class PageSpider(Spider):
    name = "link_website_crawler"
    start_urls = []
    allowed_domains = []

    def __init__(self, website_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_hrefs: set[str] = set()
        self.seen_hashes: set[str] = set()
        self.cutoff_year = datetime.now().year - 3
        self.start_urls = [website_url]
        self.allowed_domains = [website_url.split("/")[2]]

    def _is_old_link(self, href: str) -> bool:
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', href)
        return any(int(year) < self.cutoff_year for year in years)
    
    def _is_ignored_link(self, href: str) -> bool:
        return any(href.startswith(prefix) for prefix in IGNORED_HREF_PREFIXES)
        
    def parse(self, response: Response, link_text: str = ""):
        if not isinstance(response, HtmlResponse):
            return

        content = extract_content(response)
        if content:
            text_hash = sha256(content.encode("utf-8")).hexdigest()

            if text_hash in self.seen_hashes:
                self.logger.debug(f"Duplicate content hash, skipping: {response.url}")
            else:
                self.seen_hashes.add(text_hash)

                loader = ItemLoader(item=PageItem(), response=response)
                loader.default_output_processor = TakeFirst()
                loader.add_value("href_text", link_text)
                loader.add_value("href", response.url)
                loader.add_value("content", content)
                loader.add_value("source", self.allowed_domains[0])
                loader.add_value("utc", datetime.now(timezone.utc).isoformat())
                loader.add_value("hash", text_hash)
                yield loader.load_item()
                print(f"[CRAWLED] {response.url}")

        for link in response.xpath("//a[@href]"):
            href = link.attrib.get("href", "")
            text = " ".join(link.css("::text").getall()).strip()

            if not text or self._is_ignored_link(href) or self._is_old_link(href):
                continue

            abs_href = response.urljoin(href)
            abs_href = normalize_url(abs_href)

            if any(abs_href.lower().endswith(ext) for ext in EXTENSIONS):
                continue

            if PAGINATION_PATTERN.search(abs_href):
                continue

            if abs_href in self.seen_hrefs:
                continue

            self.seen_hrefs.add(abs_href)

            yield response.follow(
                abs_href,
                callback=self.parse,
                cb_kwargs={"link_text": text}
            )
