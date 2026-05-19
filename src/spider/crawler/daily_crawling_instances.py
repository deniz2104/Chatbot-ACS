from src.spider.crawler.spider_runner import SpiderRunner
from src.spider.websites import load_websites

if __name__ == "__main__":
    SpiderRunner().run(urls=load_websites())