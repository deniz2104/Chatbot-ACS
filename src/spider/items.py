import scrapy

from itemloaders.processors import MapCompose
from src.spider.content_utils import normalize_url, normalize

class PageItem(scrapy.Item):
    url_text = scrapy.Field(input_processor = MapCompose(normalize))
    url = scrapy.Field(input_processor = MapCompose(normalize_url))
    content = scrapy.Field()
    tables = scrapy.Field()
    hash = scrapy.Field()

class DocumentItem(scrapy.Item):
    document_url_text = scrapy.Field(input_processor = MapCompose(normalize))
    ## needs to be verified
    document_url = scrapy.Field(input_processor = MapCompose(normalize_url))
    document_hash = scrapy.Field()
    file_urls = scrapy.Field()
    files = scrapy.Field()