from scrapy_redis.dupefilter import RFPDupeFilter
from scrapy.utils.request import fingerprint
from scrapy import Request
from src.spider.utils import normalize_url

class NormalizedDupeFilter(RFPDupeFilter):
    def request_fingerprint(self, request: Request) -> str:
        normalized = request.replace(url=normalize_url(request.url))
        return fingerprint(normalized).hex()