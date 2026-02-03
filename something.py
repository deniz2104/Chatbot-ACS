"""
Enhanced User-Agent Scraper with Complete Browser Header Templates
Scrapes latest user agents and generates realistic, complete browser headers
"""

from typing import TypedDict
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


class BrowserHeader(TypedDict):
    """Complete browser header set with all necessary fields"""
    user_agent: str
    accept: str
    accept_language: str
    accept_encoding: str
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str
    sec_fetch_dest: str
    sec_fetch_mode: str
    sec_fetch_site: str
    sec_fetch_user: str
    upgrade_insecure_requests: str
    cache_control: str
    pragma: str
    browser: str
    os: str
    timestamp: str


BASE_WEBSITE: str = "https://www.whatismybrowser.com/guides/the-latest-user-agent/"

BROWSER_OS_MAP: dict[str, list[str]] = {
    "chrome": ["windows", "macos", "linux"],
    "firefox": ["windows", "macos", "linux"],
    "safari": ["macos", "ios"],
    "edge": ["windows", "macos"],
}


# ============================================================================
# HEADER TEMPLATES - Based on Real Browser Behavior
# ============================================================================
# These templates are built from actual browser headers captured from:
# - Chrome DevTools Network tab
# - Firefox Developer Tools
# - Safari Web Inspector
# - httpbin.org/headers testing
# ============================================================================

HEADER_TEMPLATES: dict[str, dict[str, str]] = {
    "chrome": {
        # Chrome sends extensive Accept header with image format preferences
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        
        # Chrome prefers US English by default
        "accept_language": "en-US,en;q=0.9",
        
        # Modern Chrome supports zstd compression
        "accept_encoding": "gzip, deflate, br, zstd",
        
        # Fetch metadata for navigation requests
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        # Standard cache headers
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
    
    "firefox": {
        # Firefox has simpler Accept header
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        
        # Firefox uses different language format
        "accept_language": "en-US,en;q=0.5",
        
        # Firefox doesn't support zstd yet
        "accept_encoding": "gzip, deflate, br",
        
        # Firefox Fetch metadata
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        # Standard headers
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
    
    "safari": {
        # Safari has the simplest Accept header
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        
        # Safari language header
        "accept_language": "en-US,en;q=0.9",
        
        # Safari compression support
        "accept_encoding": "gzip, deflate, br",
        
        # Safari Fetch metadata (newer versions)
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        # Standard headers
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
    
    "edge": {
        # Edge (Chromium-based) similar to Chrome
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        
        # Standard language
        "accept_language": "en-US,en;q=0.9",
        
        # Same as Chrome (Chromium-based)
        "accept_encoding": "gzip, deflate, br, zstd",
        
        # Fetch metadata
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        # Standard headers
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
}


def get_soup(url: str) -> BeautifulSoup:
    """
    Fetch and parse HTML from URL
    
    Args:
        url: URL to fetch
        
    Returns:
        BeautifulSoup object with parsed HTML
    """
    response: requests.Response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_version_from_user_agent(user_agent: str, browser: str) -> str:
    """
    Extract browser version from user agent string
    
    Args:
        user_agent: Full user agent string
        browser: Browser type (chrome, firefox, etc.)
        
    Returns:
        Major version number as string
    """
    try:
        if browser in ["chrome", "edge"]:
            # Chrome/131.0.0.0 or Edg/131.0.0.0
            if "Chrome/" in user_agent:
                version = user_agent.split("Chrome/")[1].split(".")[0]
                return version
            elif "Edg/" in user_agent:
                version = user_agent.split("Edg/")[1].split(".")[0]
                return version
        elif browser == "firefox":
            # Firefox/133.0
            if "Firefox/" in user_agent:
                version = user_agent.split("Firefox/")[1].split(".")[0]
                return version
        elif browser == "safari":
            # Version/17.5 (Safari uses this for version)
            if "Version/" in user_agent:
                version = user_agent.split("Version/")[1].split(".")[0]
                return version
    except (IndexError, AttributeError):
        pass
    
    # Fallback versions (current as of 2026)
    fallback_versions: dict[str, str] = {
        "chrome": "131",
        "firefox": "133",
        "safari": "17",
        "edge": "131",
    }
    return fallback_versions.get(browser, "100")


def generate_sec_ch_ua(browser: str, user_agent: str) -> str:
    """
    Generate Sec-CH-UA header for Chromium-based browsers
    
    This header is part of the Client Hints API and provides
    browser branding information.
    
    Args:
        browser: Browser type
        user_agent: Full user agent string
        
    Returns:
        Sec-CH-UA header value or empty string for non-Chromium browsers
    """
    version: str = extract_version_from_user_agent(user_agent, browser)
    
    if browser == "chrome":
        return f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not=A?Brand";v="24"'
    
    elif browser == "edge":
        return f'"Microsoft Edge";v="{version}", "Chromium";v="{version}", "Not=A?Brand";v="24"'
    
    else:
        # Firefox and Safari don't use Sec-CH-UA headers
        return ""


def generate_sec_ch_ua_platform(os_name: str) -> str:
    """
    Generate Sec-CH-UA-Platform header based on OS
    
    Args:
        os_name: Operating system name
        
    Returns:
        Quoted platform string
    """
    platform_map: dict[str, str] = {
        "windows": '"Windows"',
        "macos": '"macOS"',
        "linux": '"Linux"',
        "ios": '"iOS"',
        "android": '"Android"',
    }
    return platform_map.get(os_name, '"Unknown"')


def generate_sec_ch_ua_mobile(os_name: str) -> str:
    """
    Generate Sec-CH-UA-Mobile header
    
    Args:
        os_name: Operating system name
        
    Returns:
        "?1" for mobile, "?0" for desktop
    """
    mobile_os: set[str] = {"ios", "android"}
    return "?1" if os_name in mobile_os else "?0"


def create_browser_header(
    user_agent: str,
    browser: str,
    os_name: str,
) -> BrowserHeader:
    """
    Create complete browser header set from user agent
    
    This function takes a user agent string and generates all the
    accompanying headers that a real browser would send, making
    requests appear more legitimate.
    
    Args:
        user_agent: User agent string
        browser: Browser type (chrome, firefox, safari, edge)
        os_name: Operating system (windows, macos, linux, ios, android)
        
    Returns:
        Complete BrowserHeader dictionary
    """
    # Get base template for this browser
    template: dict[str, str] = HEADER_TEMPLATES.get(
        browser,
        HEADER_TEMPLATES["chrome"]  # Fallback to Chrome
    )
    
    # Generate dynamic headers based on UA and OS
    sec_ch_ua: str = generate_sec_ch_ua(browser, user_agent)
    sec_ch_ua_platform: str = generate_sec_ch_ua_platform(os_name)
    sec_ch_ua_mobile: str = generate_sec_ch_ua_mobile(os_name)
    
    # Build complete header
    header: BrowserHeader = {
        "user_agent": user_agent,
        "accept": template["accept"],
        "accept_language": template["accept_language"],
        "accept_encoding": template["accept_encoding"],
        "sec_ch_ua": sec_ch_ua,
        "sec_ch_ua_mobile": sec_ch_ua_mobile,
        "sec_ch_ua_platform": sec_ch_ua_platform,
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


def get_user_agents() -> list[tuple[str, str, str]]:
    """
    Scrape latest user agents from whatismybrowser.com
    
    Returns:
        List of (user_agent, browser, os) tuples
    """
    user_agents: list[tuple[str, str, str]] = []
    
    for browser, operating_systems in BROWSER_OS_MAP.items():
        try:
            print(f"Scraping {browser}...")
            soup: BeautifulSoup = get_soup(f"{BASE_WEBSITE}/{browser}")
            entries = soup.find_all("span", attrs={"class": "code"})
            
            # Match OS to user agent entries
            for os_name, entry in zip(operating_systems, entries, strict=False):
                user_agent_text: str = entry.text.strip()
                if user_agent_text:
                    user_agents.append((user_agent_text, browser, os_name))
                    print(f"  ✓ Found {browser}/{os_name}")
                    
        except Exception as e:
            print(f"  ✗ Error scraping {browser}: {e}")
            continue
    
    return user_agents


def scrape_and_generate_headers() -> list[BrowserHeader]:
    """
    Main function: Scrape user agents and generate complete headers
    
    Returns:
        List of complete browser headers
    """
    print("=" * 70)
    print("Scraping Latest User Agents & Generating Complete Headers")
    print("=" * 70)
    print()
    
    # Step 1: Scrape user agents
    user_agents: list[tuple[str, str, str]] = get_user_agents()
    print(f"\n✓ Successfully scraped {len(user_agents)} user agents")
    
    # Step 2: Generate complete headers
    print("\nGenerating complete browser headers...")
    headers: list[BrowserHeader] = []
    
    for user_agent, browser, os_name in user_agents:
        header: BrowserHeader = create_browser_header(user_agent, browser, os_name)
        headers.append(header)
    
    print(f"✓ Generated {len(headers)} complete header sets")
    
    return headers


def format_header_for_requests(header: BrowserHeader) -> dict[str, str]:
    """
    Convert BrowserHeader to dict suitable for requests library
    
    Args:
        header: BrowserHeader object
        
    Returns:
        Dictionary of headers ready for use with requests.get()
    """
    request_headers: dict[str, str] = {
        "User-Agent": header["user_agent"],
        "Accept": header["accept"],
        "Accept-Language": header["accept_language"],
        "Accept-Encoding": header["accept_encoding"],
        "Sec-Fetch-Dest": header["sec_fetch_dest"],
        "Sec-Fetch-Mode": header["sec_fetch_mode"],
        "Sec-Fetch-Site": header["sec_fetch_site"],
        "Sec-Fetch-User": header["sec_fetch_user"],
        "Upgrade-Insecure-Requests": header["upgrade_insecure_requests"],
        "Cache-Control": header["cache_control"],
        "Pragma": header["pragma"],
    }
    
    # Add Chromium-specific Client Hints headers
    if header["sec_ch_ua"]:
        request_headers["Sec-CH-UA"] = header["sec_ch_ua"]
        request_headers["Sec-CH-UA-Mobile"] = header["sec_ch_ua_mobile"]
        request_headers["Sec-CH-UA-Platform"] = header["sec_ch_ua_platform"]
    
    return request_headers


def print_header_sample(header: BrowserHeader) -> None:
    """Pretty print a sample header"""
    print("\n" + "=" * 70)
    print(f"Sample Header: {header['browser'].upper()} on {header['os'].upper()}")
    print("=" * 70)
    print(f"User-Agent: {header['user_agent']}")
    print(f"Accept: {header['accept']}")
    print(f"Accept-Language: {header['accept_language']}")
    print(f"Accept-Encoding: {header['accept_encoding']}")
    
    if header['sec_ch_ua']:
        print(f"Sec-CH-UA: {header['sec_ch_ua']}")
        print(f"Sec-CH-UA-Mobile: {header['sec_ch_ua_mobile']}")
        print(f"Sec-CH-UA-Platform: {header['sec_ch_ua_platform']}")
    
    print(f"Sec-Fetch-Dest: {header['sec_fetch_dest']}")
    print(f"Sec-Fetch-Mode: {header['sec_fetch_mode']}")
    print(f"Sec-Fetch-Site: {header['sec_fetch_site']}")
    print(f"Sec-Fetch-User: {header['sec_fetch_user']}")
    print(f"Upgrade-Insecure-Requests: {header['upgrade_insecure_requests']}")
    print(f"Cache-Control: {header['cache_control']}")
    print(f"Timestamp: {header['timestamp']}")
    print("=" * 70)


if __name__ == "__main__":
    import json
    
    # Scrape and generate headers
    headers = scrape_and_generate_headers()
    
    # Save to JSON file
    output_file = "browser_headers.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(headers)} headers to {output_file}")
    
    # Display samples
    if headers:
        # Show Chrome example
        chrome_headers = [h for h in headers if h["browser"] == "chrome"]
        if chrome_headers:
            print_header_sample(chrome_headers[0])
        
        # Show Firefox example
        firefox_headers = [h for h in headers if h["browser"] == "firefox"]
        if firefox_headers:
            print_header_sample(firefox_headers[0])