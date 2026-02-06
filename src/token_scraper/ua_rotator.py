from datetime import datetime
import os
from zoneinfo import ZoneInfo
import json

from src.token_scraper.header_builder import BrowserHeader
from src.token_scraper.constants import HEADER_TEMPLATES, PLATFORM_MAP

def make_docs_dir_if_not_exists() -> None:
    docs_path = "src/token_scraper/docs"
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

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


## de mutat in blob storage ulterior
def save_headers_to_json(headers: list[BrowserHeader], output_file: str = "src/token_scraper/docs/browser_headers.json") -> None:
    make_docs_dir_if_not_exists()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2, ensure_ascii=False)

## de citit tot din blob storage ulterior
def load_headers_from_json(path: str = "src/token_scraper/docs/browser_headers.json") -> list[BrowserHeader]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
