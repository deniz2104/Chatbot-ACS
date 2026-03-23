import os
import multiprocessing

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.spider.crawler.page_spider import PageSpider, SitemapPageSpider
from src.spider.utils import flush_redis
from src.spider.utils import get_urls

def _run_spider(spider_cls, kwargs):
    os.environ["SCRAPY_SETTINGS_MODULE"] = "src.spider.settings"
    settings = get_project_settings()
    flush_redis(settings.get("REDIS_URL"))
    process = CrawlerProcess(settings)
    process.crawl(spider_cls, **kwargs)
    process.start()

def run_spider(spider_cls, **kwargs):
    p = multiprocessing.Process(target=_run_spider, args=(spider_cls, kwargs))
    p.start()
    p.join()
    
def main() -> None:
    crawl_urls = get_urls(has_sitemap=False)
    sitemap_urls = get_urls(has_sitemap=True)

    if crawl_urls:
        run_spider(PageSpider, website_urls=crawl_urls)
    if sitemap_urls:
        run_spider(SitemapPageSpider, website_urls=sitemap_urls)


if __name__ == "__main__":
    main()
