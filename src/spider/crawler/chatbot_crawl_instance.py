import os

from dotenv import load_dotenv

from src.chatbot.user_query import resolve_urls
from src.chatbot.url_loader import _load_crawled_urls
from src.spider.crawler.spider_runner import SpiderRunner
from src.vector_database.vector_db import promote_current_to_previous, delete_previous

load_dotenv()

if __name__ == "__main__":
    query = "whatever"  ## will be sent from UI
    files_store = os.environ["FILES_STORE"]
    chatbot_store = os.environ["SCRAPY_FILES_STORE"]

    urls = resolve_urls(query, files_store=files_store)
    remaining_urls = [url for url in urls if url not in _load_crawled_urls(chatbot_store)]

    if remaining_urls:
        promote_current_to_previous()
        SpiderRunner(override_settings="src.crawl_settings.chatbot_settings").run(
            urls=remaining_urls, has_docs=True
        )
        delete_previous()
