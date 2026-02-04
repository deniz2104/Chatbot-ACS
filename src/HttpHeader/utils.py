BASE_WEBSITE = 'https://www.whatismybrowser.com/guides/the-latest-user-agent/'

BROWSER_OS_MAP = {
	"chrome": ["windows", "macos"],
	"firefox": ["windows", "macos"],
	"safari": ["macos"],
}

BROWSERS = list(BROWSER_OS_MAP.keys())

HEADER_TEMPLATES: dict[str, dict[str, str]] = {
    "chrome": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        
        "accept_language": "en-US,en;q=0.9",
        
        "accept_encoding": "gzip, deflate, br, zstd",
        
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
    
    "firefox": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        
        "accept_language": "en-US,en;q=0.5",
        
        "accept_encoding": "gzip, deflate, br",
    
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    },
    
    "safari": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        
        "accept_language": "en-US,en;q=0.9",
        
        "accept_encoding": "gzip, deflate, br",
        
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
        
        "upgrade_insecure_requests": "1",
        "cache_control": "max-age=0",
        "pragma": "no-cache",
    }
}

PLATFORM_MAP: dict[str, str] = {
    "windows": '"Windows"',
    "macos": '"macOS"'
}