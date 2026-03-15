import os

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.environ.get("SCRAPY_BOT_NAME")

OUTPUT_PATH = os.environ.get("SCRAPY_OUTPUT_PATH")

SPIDER_MODULES = ["src.spider.crawler"]

ROBOTSTXT_OBEY = os.getenv("SCRAPY_ROBOTSTXT_OBEY", "true").strip().lower() == "true"

REDIS_URL = os.environ.get("REDIS_URL")
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "src.spider.link_duplicates.NormalizedDupeFilter"
SCHEDULER_PERSIST = os.getenv("SCRAPY_SCHEDULER_PERSIST", "false").strip().lower() == "true"

CONCURRENT_REQUESTS = int(os.environ.get("SCRAPY_CONCURRENT_REQUESTS", "32"))
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.environ.get("SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN", "16"))
DOWNLOAD_DELAY = 0

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0

COOKIES_ENABLED = os.getenv("SCRAPY_COOKIES_ENABLED", "false").strip().lower() == "true"

ITEM_PIPELINES = {
    "src.spider.pipelines.ValidationPipeline": 100,
    "src.spider.pipelines.DeduplicationPipeline": 200,
    "src.spider.pipelines.MergePipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "src.spider.middlewares.RotatingHeadersMiddleware": 400,
}

LOG_LEVEL = os.environ.get("SCRAPY_LOG_LEVEL", "INFO")

RETRY_ENABLED = os.getenv("SCRAPY_RETRY_ENABLED", "true").strip().lower() == "true"
RETRY_TIMES = int(os.environ.get("SCRAPY_RETRY_TIMES", "2"))
RETRY_HTTP_CODES = [
    int(code.strip())
    for code in os.getenv("SCRAPY_RETRY_HTTP_CODES", "500,502,503,504,408,429").split(",")
    if code.strip()
]

DEPTH_LIMIT = int(os.environ.get("SCRAPY_DEPTH_LIMIT", "50"))

CLOSESPIDER_TIMEOUT = int(os.environ.get("SCRAPY_CLOSESPIDER_TIMEOUT", "1800"))
CLOSESPIDER_ERRORCOUNT = int(os.environ.get("SCRAPY_CLOSESPIDER_ERRORCOUNT", "50"))

DNS_TIMEOUT = int(os.environ.get("SCRAPY_DNS_TIMEOUT", "30"))
DOWNLOAD_TIMEOUT = int(os.environ.get("SCRAPY_DOWNLOAD_TIMEOUT", "15"))

REACTOR_THREADPOOL_MAXSIZE = 20
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 500

DOWNLOADER_CLIENTCONTEXTFACTORY = "src.spider.ssl_context.CustomContextFactory"
