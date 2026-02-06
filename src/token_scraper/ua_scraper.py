from bs4 import BeautifulSoup
import requests

from src.token_scraper.header_builder import BrowserHeader
from src.token_scraper.constants import BASE_WEBSITE, BROWSER_OS_MAP
from src.token_scraper.ua_rotator import create_browser_header
from src.token_scraper.fake_ua import generate_random_ua


def website_response(url: str) -> BeautifulSoup:
    response: requests.Response = requests.get(url, headers= generate_random_ua(), timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape_user_agents() -> list[tuple[str, str, str]]:
    user_agents: list[tuple[str, str, str]] = []

    for browser, operating_systems in BROWSER_OS_MAP.items():
        try:
            print(f"Scraping {browser}...")
            soup: BeautifulSoup = website_response(f"{BASE_WEBSITE}/{browser}")
            entries = soup.find_all("span", attrs={"class": "code"})

            for os_name, entry in zip(operating_systems, entries, strict=False):
                user_agent_text: str = entry.text.strip()
                if user_agent_text:
                    user_agents.append((user_agent_text, browser, os_name))
                    print(f"Found {browser}/{os_name}")

        except Exception as e:
            print(f"Error scraping {browser}: {e}")
            continue

    return user_agents


def scrape_and_generate_headers() -> list[BrowserHeader]:
    print("=" * 70)
    print("Scraping User Agents And Generating Headers")
    print("=" * 70)
    print()

    user_agents: list[tuple[str, str, str]] = scrape_user_agents()
    print(f"\nSuccessfully scraped {len(user_agents)} user agents")

    print("\nGenerating complete browser headers...")
    headers: list[BrowserHeader] = []

    for user_agent, browser, os_name in user_agents:
        header: BrowserHeader = create_browser_header(user_agent, browser, os_name)
        headers.append(header)

    print(f"Generated {len(headers)} complete headers")

    return headers
