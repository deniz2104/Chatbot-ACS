import scrapy

from itemloaders.processors import MapCompose
from src.spider.utils import normalize_url

class PageItem(scrapy.Item):
    href_text = scrapy.Field(input_processor = MapCompose(lambda x: x.strip() if x else ""))
    href = scrapy.Field(input_processor = MapCompose(normalize_url))
    content = scrapy.Field()
    source = scrapy.Field()
    utc = scrapy.Field()
    hash = scrapy.Field()

class DocumentItem(scrapy.Item):
    document_href_text = scrapy.Field(input_processor = MapCompose(lambda x: x.strip() if x else ""))
    document_href = scrapy.Field()
    document_category = scrapy.Field()
    document_utc = scrapy.Field()
    document_hash = scrapy.Field()