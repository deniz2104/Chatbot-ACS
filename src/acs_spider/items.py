import scrapy

class AcsPageItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    headings = scrapy.Field()
    links = scrapy.Field()
