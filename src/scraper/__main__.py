import argparse
import os

from src.scraper.ua_rotator import load_headers_from_json, save_headers_to_json
from src.scraper.ua_scraper import scrape_and_generate_headers
from src.scraper.scraper import BrowserHeaderScraper

CACHE_PATH = "src/scraper/docs/browser_headers.json"


def example_full_scraping_workflow(refresh: bool = False) -> None:
    if refresh or not os.path.exists(CACHE_PATH):
        print("Scraping fresh headers from the web...")
        headers = scrape_and_generate_headers()
        save_headers_to_json(headers)
        print(f"\nSaved {len(headers)} headers to {CACHE_PATH}")
    else:
        print(f"Loading cached headers from {CACHE_PATH}")
        headers = load_headers_from_json(CACHE_PATH)
        print(f"Loaded {len(headers)} headers from cache")

    scraper = BrowserHeaderScraper(headers)

    print("\nRandom header sample:")
    sample = scraper.get_random_header()
    for key, value in sample.items():
        print(f"  {key}: {value}")

    url = "https://httpbin.org/headers"
    print(f"\nScraping {url}...")
    result = scraper.scrape(url)
    if result:
        print(f"Got {len(result)} characters of content")


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser header scraper demo")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-scrape headers from the web instead of using cache",
    )
    args = parser.parse_args()
    example_full_scraping_workflow(refresh=args.refresh)


if __name__ == "__main__":
    main()
