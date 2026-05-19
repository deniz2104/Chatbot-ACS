import os

from dotenv import load_dotenv

load_dotenv()

DEPTH_LIMIT = 2
FILES_STORE = os.environ.get("SCRAPY_FILES_STORE")

ITEM_PIPELINES = {
    "src.spider.pipelines.ValidationPipeline": 100,
    "src.spider.pipelines.DeduplicationPipeline": 200,
    "src.spider.pipelines.DocumentFilesPipeline": 300,
    "src.spider.pipelines.ChatbotOutputPipeline": 400,
    "src.spider.pipelines.ContentChunkingPipeline": 500,
}

DOWNLOADER_CLIENTCONTEXTFACTORY = "src.spider.ssl_context.CustomContextFactory"