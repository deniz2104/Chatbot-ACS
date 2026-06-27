import logging

from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

from src.spider.crawler.page_spider import PageSpider
from src.azure.redis.redis_utils import flush_redis
from src.spider.constants import urls
from src.vector_database.vector_db import (
    start_crawl, get_crawl_ids, get_all_url_chunk_ids, delete_chunks
)

logger = logging.getLogger(__name__)


class SpiderRunner:
    def __init__(self, main_settings: str = "src.spider.settings") -> None:
        self._settings = Settings()
        self._settings.setmodule(main_settings, priority="project")

    def run(self, start_urls: list[str]) -> None:
        if self._settings.get("REDIS_URL"):
            flush_redis(redis_url=self._settings["REDIS_URL"])

        existing = get_all_url_chunk_ids()
        logger.info("[CRAWL] ChromaDB snapshot: %d known URL(s)", len(existing))

        start_crawl()

        logger.info("Starting crawler for %d URL(s): %s", len(start_urls), start_urls)
        process = CrawlerProcess(self._settings)
        process.crawl(PageSpider, start_urls=start_urls)
        process.start()
        logger.info("Crawler process finished")

        self._reconcile(existing)

    def _reconcile(self, existing: dict[str, set[str]]) -> None:
        crawled = get_crawl_ids()
        existing_urls = set(existing)
        crawled_urls = set(crawled)

        new_urls = crawled_urls - existing_urls
        removed_urls = existing_urls - crawled_urls
        changed_urls: set[str] = set()
        unchanged_urls: set[str] = set()

        stale_ids: list[str] = []
        for url in crawled_urls & existing_urls:
            stale = existing[url] - crawled[url]
            if stale:
                stale_ids.extend(stale)
                changed_urls.add(url)
            else:
                unchanged_urls.add(url)

        removed_ids = [cid for url in removed_urls for cid in existing[url]]

        delete_chunks(stale_ids + removed_ids)

        logger.info(
            "[CRAWL] Result — new: %d | changed: %d | unchanged: %d | removed: %d",
            len(new_urls), len(changed_urls), len(unchanged_urls), len(removed_urls),
        )
        for url in sorted(new_urls):
            logger.info("[NEW]       %s", url)
        for url in sorted(changed_urls):
            logger.info("[CHANGED]   %s", url)
        for url in sorted(removed_urls):
            logger.info("[REMOVED]   %s", url)

    def crawl(self, start_urls: list[str] = urls) -> None:
        self.run(start_urls)

if __name__ == "__main__":
    runner = SpiderRunner()
    runner.crawl()
