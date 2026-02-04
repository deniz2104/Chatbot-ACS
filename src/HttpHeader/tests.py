import random
from typing import Optional
import requests

from src.HttpHeader.generate_browser_header_agent import (
    BrowserHeader,
    create_browser_header,
    scrape_user_agents,
)
from src.HttpHeader.format_header_to_request_header import format_header_for_requests
    
class BrowserHeaderScraper:
    """Scraper with built-in header rotation"""
        
    def __init__(self) -> None:
        user_agents = scrape_user_agents()
        self.headers_pool: list[BrowserHeader] = [
            create_browser_header(ua, browser, os)
            for ua, browser, os in user_agents
        ]
        
    def get_random_header(self) -> dict[str, str]:

        header = random.choice(self.headers_pool)
        return format_header_for_requests(header)
        
    def scrape(self, url: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:

                header = self.get_random_header()
                    
                print(f"Attempt {attempt + 1}/{max_retries}: {url}")
                    
                response = requests.get(url, headers=header, timeout=10)
                response.raise_for_status()
                    
                print(f"Success ({response.status_code})")
                return response.text
                    
            except requests.RequestException as e:
                print(f"Failed: {e}")
                if attempt == max_retries - 1:
                    print(f"Giving up after {max_retries} attempts")
                    return None
                print(f"Retrying with different headers...")
            
        return None
    
def example_full_scraping_workflow() -> None:
    
    scraper = BrowserHeaderScraper()
    
    urls = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
    ]

    for url in urls:
        content = scraper.scrape(url)
        if content:
            print("Successfully scraped content")


def main() -> None:
    example_full_scraping_workflow()

if __name__ == "__main__":
    main()