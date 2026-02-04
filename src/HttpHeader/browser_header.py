from typing import TypedDict

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