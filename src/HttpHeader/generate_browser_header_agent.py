from datetime import datetime
import os
from zoneinfo import ZoneInfo
import json
import requests
from bs4 import BeautifulSoup
from src.HttpHeader.utils import BASE_WEBSITE, BROWSER_OS_MAP, HEADER_TEMPLATES, PLATFORM_MAP
from src.HttpHeader.browser_header import BrowserHeader

def make_docs_dir_if_not_exists() -> None:
    docs_path = "src/HttpHeader/docs"
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

def website_response(url: str) -> BeautifulSoup:
    response: requests.Response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_version_from_user_agent(user_agent: str, browser: str) -> str:
    if browser  == "chrome":
        if "Chrome/" in user_agent:
            version = user_agent.split("Chrome/")[1].split(".")[0]
            return version
        
    return ""

def generate_sec_ch_ua(version: str, browser:str) -> str:
    return f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not=A?Brand";v="24"' if browser == "chrome" else ""


def generate_sec_ch_ua_platform(os_name: str, browser:str) -> str:
    if browser == "chrome":
        return PLATFORM_MAP.get(os_name, '"Unknown"')
    
    return '"Unknown"'

def create_browser_header(
    user_agent: str,
    browser: str,
    os_name: str,
) -> BrowserHeader:
    
    template: dict[str, str] = HEADER_TEMPLATES.get(
        browser,
        HEADER_TEMPLATES["chrome"]
    )
    
    version: str = extract_version_from_user_agent(user_agent, browser)
    sec_ch_ua: str = generate_sec_ch_ua(version, browser)
    sec_ch_ua_platform: str = generate_sec_ch_ua_platform(os_name, browser)
    
    header: BrowserHeader = {
        "user_agent": user_agent,
        "accept": template["accept"],
        "accept_language": template["accept_language"],
        "accept_encoding": template["accept_encoding"],
        "sec_ch_ua": sec_ch_ua,
        "sec_ch_ua_mobile": "?0",
        "sec_ch_ua_platform": sec_ch_ua_platform if sec_ch_ua_platform != '"Unknown"' else "",
        "sec_fetch_dest": template["sec_fetch_dest"],
        "sec_fetch_mode": template["sec_fetch_mode"],
        "sec_fetch_site": template["sec_fetch_site"],
        "sec_fetch_user": template["sec_fetch_user"],
        "upgrade_insecure_requests": template["upgrade_insecure_requests"],
        "cache_control": template["cache_control"],
        "pragma": template["pragma"],
        "browser": browser,
        "os": os_name,
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
    }
    
    return header


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

def save_headers_to_json(headers: list[BrowserHeader], output_file: str = "src/HttpHeader/docs/browser_headers.json") -> None:
    make_docs_dir_if_not_exists()
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2, ensure_ascii=False)
    
def main() -> None:
    headers = scrape_and_generate_headers()
    save_headers_to_json(headers)

if __name__ == "__main__":
    main()