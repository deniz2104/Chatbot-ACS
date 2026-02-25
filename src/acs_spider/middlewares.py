from src.token_scraper.header_builder import build_request_headers

class RotatingHeadersMiddleware:
    def process_request(self, request, spider):
        headers = build_request_headers()
        for key, value in headers.items():
            request.headers[key] = value
