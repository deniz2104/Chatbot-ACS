from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from src.spider.crawler.page_spider import PageSpider
from src.spider.redis_utils import flush_redis
from src.spider.websites import Website
from src.crawl_settings.constants import GENERAL_SETTINGS
import logging

logger = logging.getLogger(__name__)

class SpiderRunner:
    def __init__(self, main_settings: str = GENERAL_SETTINGS, override_settings: str | None = None) -> None:
        self._settings = Settings()
        self._settings.setmodule(main_settings, priority="project")
        if override_settings:
            self._settings.setmodule(override_settings, priority="spider")

        self._settings_module = main_settings if not override_settings else override_settings
        self._settings.set("SETTINGS_MODULE", self._settings_module, priority="spider")

    def run(self, urls: list[str] | list[Website], has_docs : bool = False) -> None:
        if self._settings.get("REDIS_URL"):
            flush_redis(redis_url=self._settings["REDIS_URL"])

        websites: list[Website] = []

        if urls and isinstance(urls[0], Website) and self._settings.get("SETTINGS_MODULE") == GENERAL_SETTINGS:
            websites = [site for site in urls if isinstance(site, Website)]
            urls = [site.url for site in websites]

        if not urls:
            logger.warning("No URLs provided — skipping crawl")
            return

        logger.info("Starting crawler for %d URL(s): %s", len(urls), urls)
        process = CrawlerProcess(self._settings)
        process.crawl(PageSpider, start_urls=urls, has_docs=has_docs, websites=websites)
        process.start()
        logger.info("Crawler process finished")