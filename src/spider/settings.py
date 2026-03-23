import os

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.environ.get("SCRAPY_BOT_NAME")

OUTPUT_PATH = os.environ.get("SCRAPY_OUTPUT_PATH")
DOCUMENTS_OUTPUT_PATH = os.environ.get("SCRAPY_DOCUMENTS_OUTPUT_PATH")

SPIDER_MODULES = ["src.spider.crawler"]

ROBOTSTXT_OBEY = True

REDIS_URL = os.environ.get("REDIS_URL")
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "src.spider.link_duplicates.NormalizedDupeFilter"
SCHEDULER_PERSIST = False

CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 32
DOWNLOAD_DELAY = 0

COOKIES_ENABLED = True

ITEM_PIPELINES = {
    "src.spider.pipelines.ValidationPipeline": 100,
    "src.spider.pipelines.DeduplicationPipeline": 200,
    "src.spider.pipelines.DocumentHashPipeline": 250,
    "src.spider.pipelines.MergePipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "src.spider.middlewares.RotatingHeadersMiddleware": 400,
}

LOG_LEVEL = os.environ.get("SCRAPY_LOG_LEVEL")

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500,502,503,504,408,421,429]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.25
AUTOTHROTTLE_MAX_DELAY = 3.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0

DEPTH_LIMIT = 25

CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_ERRORCOUNT = 20

DNS_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 15

REACTOR_THREADPOOL_MAXSIZE = 20
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 500

DOWNLOADER_CLIENTCONTEXTFACTORY = "src.spider.ssl_context.CustomContextFactory"
