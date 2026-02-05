import random
from typing import Optional
import requests

from src.scraper.header_builder import BrowserHeader, format_header_for_requests
from src.scraper.http_client import CustomHttpAdapter
from src.scraper.retry import RetryConfig, RetryHandler


class BrowserHeaderScraper:
    """Scraper with built-in header rotation"""

    def __init__(
        self,
        headers_pool: list[BrowserHeader],
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self.headers_pool = headers_pool
        self.session = requests.Session()
        self.session.mount('https://', CustomHttpAdapter())
        self._retry = RetryHandler(retry_config)

    def get_random_header(self) -> dict[str, str]:
        header = random.choice(self.headers_pool)
        return format_header_for_requests(header)

    def scrape(self, url: str, max_retries: int = 3) -> Optional[str]:
        config = RetryConfig(
            max_retries=max_retries,
            backoff_factor=self._retry.config.backoff_factor,
            timeout=self._retry.config.timeout,
            retryable_status_codes=self._retry.config.retryable_status_codes,
        )
        handler = RetryHandler(config)

        initial_headers = self.get_random_header()

        def _rotate_headers(attempt, _reason):
            return self.get_random_header()

        response = handler.execute(
            self.session,
            url,
            headers=initial_headers,
            on_retry=_rotate_headers,
        )

        if response is not None:
            return response.text
        return None
