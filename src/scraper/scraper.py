import random
from typing import Optional
import requests

from src.scraper.header_builder import BrowserHeader, format_header_for_requests
from src.scraper.http_client import CustomHttpAdapter

class BrowserHeaderScraper:
    """Scraper with built-in header rotation"""

    def __init__(self, headers_pool: list[BrowserHeader]) -> None:
        self.headers_pool = headers_pool
        self.session = requests.Session()
        self.session.mount('https://', CustomHttpAdapter())

    def get_random_header(self) -> dict[str, str]:

        header = random.choice(self.headers_pool)
        return format_header_for_requests(header)

    def scrape(self, url: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:

                header = self.get_random_header()

                print(f"Attempt {attempt + 1}/{max_retries}: {url}")

                response = self.session.get(url, headers=header, timeout=10,verify=False)
                response.raise_for_status()

                print(f"Success ({response.status_code})")
                return response.text

            except requests.RequestException as e:
                print(f"Failed: {e}")
                if attempt == max_retries - 1:
                    print(f"Giving up after {max_retries} attempts")
                    return None
                print("Retrying with different headers...")

        return None
