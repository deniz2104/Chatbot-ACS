import re
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse

from scrapy.spiders import CrawlSpider, SitemapSpider, Rule
from scrapy.http import Response, HtmlResponse
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from itemloaders.processors import TakeFirst

from src.spider.items import PageItem, DocumentItem
from src.spider.constants import EXT_PATTERN, MIN_YEAR, DENY_PATTERNS
from src.spider.utils import extract_content, normalize
from src.content_verification.docs_writer import DocsWriter

## Am de pus un camp custom pentru fiecare website daca facem skip la paginare cand introducem in json sau nu
## Sa gasesc o solutie de a compara doua texte. Am de facut asta pentru texte din acelasi txt cat si cu texte din alte txt-uri.

class PageParserMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_processor = TakeFirst()
        self.docs_writer = DocsWriter()
        self._year_deny = re.compile(rf"(?<!\d)({self._build_year_deny_pattern(MIN_YEAR)})(?!\d)")
        self._deny_re = re.compile("|".join(DENY_PATTERNS))

    def parse_document(self, response: Response):
        loader = ItemLoader(item=DocumentItem())
        loader.default_output_processor = self.default_processor
        loader.add_value("document_href", response.url)
        loader.add_value("document_utc", datetime.now(timezone.utc).isoformat())
        loader.add_value("document_hash", sha256(response.body).hexdigest())
        yield loader.load_item()
        self.logger.info(f"[DOC] {response.url}")

    def parse_page(self, response: Response):
        if not isinstance(response, HtmlResponse):
            return

        content = extract_content(response)
        if not content:
            return

        self.docs_writer.add_content(content, response.url)

        loader = ItemLoader(item=PageItem(), response=response)
        loader.default_output_processor = self.default_processor
        loader.add_value("href_text", response.meta.get("link_text", ""))
        loader.add_value("href", response.url)
        loader.add_value("content", content)
        loader.add_value("utc", datetime.now(timezone.utc).isoformat())
        loader.add_value("hash", sha256(normalize(content).encode("utf-8")).hexdigest())

        yield loader.load_item()
        self.logger.info(f"[CRAWLED] {response.url}")

        doc_extractor = getattr(self, "_doc_extractor", None)
        if doc_extractor:
            for link in doc_extractor.extract_links(response):
                yield response.follow(link.url, callback=self.parse_document)

    def closed(self, _reason):
        self.docs_writer.flush_buffers()

    def _should_deny_url(self, url: str) -> bool:
        return bool(self._deny_re.search(url) or self._year_deny.search(url))

    @staticmethod
    def _build_year_deny_pattern(min_year: int = MIN_YEAR) -> str:
        decade = min_year % 100 // 10
        parts = [r"19\d{2}"]
        parts += [f"20{d}\\d" for d in range(0, decade)]
        if min_year % 10 > 0:
            parts.append(
                f"20{decade}[0-{min_year % 10 - 1}]"
            )
        return "|".join(parts)


class PageSpider(PageParserMixin, CrawlSpider):
    name = "link_website_crawler"
    start_urls : list[str] = []
    allowed_domains : list[str] = []
    
    def __init__(self, website_urls: list[str], *args, **kwargs):
        PageParserMixin.__init__(self, *args, **kwargs)
        self.start_urls = website_urls
        self.allowed_domains = [
            url.split("/")[2] for url in website_urls
        ]

        self._doc_extractor = LinkExtractor(
            allow=EXT_PATTERN,
            allow_domains=self.allowed_domains,
            unique=True,
        )

        self.rules = (
            Rule(
                LinkExtractor(
                    deny=(self._deny_re, self._year_deny, EXT_PATTERN),
                    allow_domains=self.allowed_domains,
                    unique=True,
                    canonicalize=True,
                ),
                callback="parse_page",
                follow=True,
                process_links="_filter_links",
            ),
        )

        CrawlSpider.__init__(self, *args, **kwargs)

    def _filter_links(self, links):
        return [link for link in links if urlparse(link.url).hostname in self.allowed_domains]

class SitemapPageSpider(PageParserMixin, SitemapSpider):
    name = "sitemap_website_crawler"
    start_urls : list[str] = []
    allowed_domains : list[str] = []
    sitemap_urls : list[str] = []
    sitemap_rules : list[tuple] = []

    def __init__(self, website_urls: list[str], *args, **kwargs):
        PageParserMixin.__init__(self, *args, **kwargs)
        self.allowed_domains = [
            url.split("/")[2] for url in website_urls
        ]
        self.sitemap_urls = [
            url.rstrip("/") + "/sitemap.xml" for url in website_urls
        ]
        self.sitemap_rules = [
        (EXT_PATTERN, "parse_document"),
        ("", "parse_page"),
    ]

        SitemapSpider.__init__(self, *args, **kwargs)

    def sitemap_filter(self, entries):
        for entry in entries:
            url = entry["loc"]
            if self._should_deny_url(url):
                continue
            yield entry