import random
from src.token_scraper.ua_rotator import load_headers_from_json
from src.token_scraper.header_builder import format_header_for_requests

class RotatingHeadersMiddleware:
    def __init__(self):
        print("[3. MIDDLEWARE INIT] Loading browser headers from JSON...")
        self.headers_pool = load_headers_from_json()
        print(f"[3. MIDDLEWARE INIT] Loaded {len(self.headers_pool)} header profiles into pool")
        self.request_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        print("[3. MIDDLEWARE INIT] Scrapy called from_crawler() -> instantiating RotatingHeadersMiddleware")
        return cls()

    def process_request(self, request):
        self.request_count += 1
        header = random.choice(self.headers_pool)
        formatted = format_header_for_requests(header)
        print(f"\n[4. MIDDLEWARE] Request #{self.request_count} -> {request.url}")
        print(f"[4. MIDDLEWARE]   User-Agent: {formatted['User-Agent'][:70]}...")
        print(f"[4. MIDDLEWARE]   Browser: {header['browser']} | OS: {header['os']}")
        for key, value in formatted.items():
            request.headers[key] = value
        return None
