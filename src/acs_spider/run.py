import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.acs_spider.spiders.acs_spider import AcsSpider


def main():
    print("\n[1. STARTUP] Loading project settings from settings.py...")
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "src.acs_spider.settings")
    settings = get_project_settings()
    print(f"[1. STARTUP] Settings loaded. Bot name: {settings.get('BOT_NAME')}")
    print(f"[1. STARTUP] Concurrent requests: {settings.get('CONCURRENT_REQUESTS')}")
    print(f"[1. STARTUP] Download delay: {settings.get('DOWNLOAD_DELAY')}s")
    print(f"[1. STARTUP] Retry enabled: {settings.get('RETRY_ENABLED')} (max {settings.get('RETRY_TIMES')} times)")
    print(f"[1. STARTUP] Middlewares: {dict(settings.get('DOWNLOADER_MIDDLEWARES', {}))}")

    print("\n[2. CRAWLER] Creating CrawlerProcess and registering AcsSpider...")
    process = CrawlerProcess(settings)
    process.crawl(AcsSpider)

    print("[2. CRAWLER] Starting the Twisted reactor (event loop)...\n")
    process.start()
    print("\n[DONE] Reactor stopped. Scraping finished.")


if __name__ == "__main__":
    main()
