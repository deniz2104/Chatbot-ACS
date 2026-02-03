"""
Practical Examples: Using Complete Browser Headers
Demonstrates how to use the generated headers in real scraping scenarios
"""

import json
import random
from typing import Optional

import requests

from something import (
    BrowserHeader,
    create_browser_header,
    format_header_for_requests, 
    get_user_agents,
)


def example_1_basic_usage() -> None:
    """Example 1: Basic usage - scrape with one complete header set"""
    print("\n" + "=" * 70)
    print("Example 1: Basic Usage - Single Request with Complete Headers")
    print("=" * 70)
    
    # Step 1: Scrape a user agent
    user_agents = get_user_agents()
    if not user_agents:
        print("Error: No user agents scraped")
        return
    
    # Pick first Chrome/Windows combination
    chrome_ua = next(
        (ua for ua in user_agents if ua[1] == "chrome" and ua[2] == "windows"),
        user_agents[0]
    )
    
    user_agent, browser, os_name = chrome_ua
    
    # Step 2: Generate complete headers
    header: BrowserHeader = create_browser_header(user_agent, browser, os_name)
    
    # Step 3: Format for requests
    request_headers: dict[str, str] = format_header_for_requests(header)
    
    # Step 4: Make request
    print(f"\nUsing: {browser}/{os_name}")
    print(f"UA: {user_agent[:60]}...")
    
    try:
        response = requests.get('https://httpbin.org/headers', headers=request_headers)
        result = response.json()
        
        print(f"\n✓ Request successful!")
        print(f"Status: {response.status_code}")
        print(f"\nHeaders sent:")
        for key, value in result['headers'].items():
            print(f"  {key}: {value[:70]}..." if len(value) > 70 else f"  {key}: {value}")
    except requests.RequestException as e:
        print(f"✗ Request failed: {e}")


def example_2_header_rotation() -> None:
    """Example 2: Rotate headers between requests"""
    print("\n" + "=" * 70)
    print("Example 2: Header Rotation - Different Header Per Request")
    print("=" * 70)
    
    # Scrape all user agents
    user_agents = get_user_agents()
    if not user_agents:
        print("Error: No user agents scraped")
        return
    
    # Create headers for each user agent
    headers_pool: list[BrowserHeader] = []
    for user_agent, browser, os_name in user_agents:
        header = create_browser_header(user_agent, browser, os_name)
        headers_pool.append(header)
    
    print(f"Generated {len(headers_pool)} header sets")
    
    # Make multiple requests with different headers
    urls = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
        'https://httpbin.org/user-agent',
    ]
    
    print(f"\nMaking {len(urls)} requests with rotating headers:")
    
    for idx, url in enumerate(urls, 1):
        # Pick random header
        header = random.choice(headers_pool)
        request_headers = format_header_for_requests(header)
        
        try:
            response = requests.get(url, headers=request_headers)
            result = response.json()
            
            user_agent_sent = result.get('user-agent', result.get('headers', {}).get('User-Agent', 'N/A'))
            
            print(f"\n[{idx}] {header['browser']}/{header['os']}")
            print(f"    URL: {url}")
            print(f"    UA: {user_agent_sent[:60]}...")
            print(f"    Status: {response.status_code}")
        except requests.RequestException as e:
            print(f"\n[{idx}] ✗ Failed: {e}")


def example_3_browser_specific() -> None:
    """Example 3: Use specific browser type"""
    print("\n" + "=" * 70)
    print("Example 3: Browser-Specific Headers")
    print("=" * 70)
    
    user_agents = get_user_agents()
    if not user_agents:
        print("Error: No user agents scraped")
        return
    
    # Test with different browsers
    browsers_to_test = ["chrome", "firefox", "safari"]
    
    for browser in browsers_to_test:
        # Find user agent for this browser
        browser_ua = next(
            (ua for ua in user_agents if ua[1] == browser),
            None
        )
        
        if not browser_ua:
            print(f"\n✗ No {browser} user agent found")
            continue
        
        user_agent, _, os_name = browser_ua
        header = create_browser_header(user_agent, browser, os_name)
        request_headers = format_header_for_requests(header)
        
        print(f"\n--- Testing {browser.upper()} ---")
        print(f"OS: {os_name}")
        print(f"UA: {user_agent[:60]}...")
        
        # Check key differences
        if header['sec_ch_ua']:
            print(f"Sec-CH-UA: {header['sec_ch_ua']}")
        else:
            print("Sec-CH-UA: Not sent (Firefox/Safari)")
        
        print(f"Accept: {header['accept'][:60]}...")
        print(f"Accept-Language: {header['accept_language']}")


def example_4_custom_headers() -> None:
    """Example 4: Customize headers for specific needs"""
    print("\n" + "=" * 70)
    print("Example 4: Customizing Headers")
    print("=" * 70)
    
    user_agents = get_user_agents()
    if not user_agents:
        print("Error: No user agents scraped")
        return
    
    # Get a base header
    user_agent, browser, os_name = user_agents[0]
    header = create_browser_header(user_agent, browser, os_name)
    request_headers = format_header_for_requests(header)
    
    print("\n1. Original headers (US English):")
    print(f"   Accept-Language: {request_headers['Accept-Language']}")
    
    # Customize for different region
    request_headers['Accept-Language'] = 'fr-FR,fr;q=0.9,en;q=0.8'
    print("\n2. Modified for French user:")
    print(f"   Accept-Language: {request_headers['Accept-Language']}")
    
    # Add custom headers
    request_headers['DNT'] = '1'  # Do Not Track
    request_headers['Connection'] = 'keep-alive'
    print("\n3. Added custom headers:")
    print(f"   DNT: {request_headers['DNT']}")
    print(f"   Connection: {request_headers['Connection']}")
    
    # Add Referer for non-direct navigation
    request_headers['Referer'] = 'https://www.google.com/'
    request_headers['Sec-Fetch-Site'] = 'cross-site'
    print("\n4. Simulating navigation from Google:")
    print(f"   Referer: {request_headers['Referer']}")
    print(f"   Sec-Fetch-Site: {request_headers['Sec-Fetch-Site']}")


def example_5_save_and_load() -> None:
    """Example 5: Save headers to file and load later"""
    print("\n" + "=" * 70)
    print("Example 5: Saving and Loading Headers")
    print("=" * 70)
    
    # Generate headers
    user_agents = get_user_agents()
    headers_pool: list[BrowserHeader] = []
    
    for user_agent, browser, os_name in user_agents[:5]:  # First 5
        header = create_browser_header(user_agent, browser, os_name)
        headers_pool.append(header)
    
    # Save to JSON
    filename = "my_headers.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(headers_pool, f, indent=2)
    
    print(f"✓ Saved {len(headers_pool)} headers to {filename}")
    
    # Load from JSON
    with open(filename, 'r', encoding='utf-8') as f:
        loaded_headers: list[BrowserHeader] = json.load(f)
    
    print(f"✓ Loaded {len(loaded_headers)} headers from {filename}")
    
    # Use loaded header
    if loaded_headers:
        header = loaded_headers[0]
        request_headers = format_header_for_requests(header)
        
        print(f"\nUsing loaded header:")
        print(f"  Browser: {header['browser']}")
        print(f"  OS: {header['os']}")
        print(f"  Timestamp: {header['timestamp']}")


def example_6_full_scraping_workflow() -> None:
    """Example 6: Complete scraping workflow with error handling"""
    print("\n" + "=" * 70)
    print("Example 6: Complete Scraping Workflow")
    print("=" * 70)
    
    class BrowserHeaderScraper:
        """Scraper with built-in header rotation"""
        
        def __init__(self) -> None:
            user_agents = get_user_agents()
            self.headers_pool: list[BrowserHeader] = [
                create_browser_header(ua, browser, os)
                for ua, browser, os in user_agents
            ]
            print(f"Initialized with {len(self.headers_pool)} header sets")
        
        def get_random_header(self) -> dict[str, str]:
            """Get random header set"""
            header = random.choice(self.headers_pool)
            return format_header_for_requests(header)
        
        def scrape(self, url: str, max_retries: int = 3) -> Optional[str]:
            """Scrape URL with retry logic"""
            for attempt in range(max_retries):
                try:
                    # Get fresh headers for each attempt
                    headers = self.get_random_header()
                    
                    print(f"  Attempt {attempt + 1}/{max_retries}: {url}")
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    print(f"  ✓ Success ({response.status_code})")
                    return response.text
                    
                except requests.RequestException as e:
                    print(f"  ✗ Failed: {e}")
                    if attempt == max_retries - 1:
                        print(f"  Giving up after {max_retries} attempts")
                        return None
                    print(f"  Retrying with different headers...")
            
            return None
    
    # Use the scraper
    scraper = BrowserHeaderScraper()
    
    # Scrape multiple URLs
    urls = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
    ]
    
    print(f"\nScraping {len(urls)} URLs:")
    for url in urls:
        content = scraper.scrape(url)
        if content:
            print(f"  Retrieved {len(content)} bytes\n")


def main() -> None:
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Complete Browser Headers - Practical Examples")
    print("=" * 70)
    
    try:
        example_1_basic_usage()
        example_2_header_rotation()
        example_3_browser_specific()
        example_4_custom_headers()
        example_5_save_and_load()
        example_6_full_scraping_workflow()
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()