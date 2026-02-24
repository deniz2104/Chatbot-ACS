from typing import TypedDict

class BrowserHeader(TypedDict):
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


def format_header_for_requests(header: BrowserHeader) -> dict[str, str]:
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

    if header["sec_ch_ua"]:
        request_headers["Sec-CH-UA"] = header["sec_ch_ua"]
        request_headers["Sec-CH-UA-Mobile"] = header["sec_ch_ua_mobile"]
        request_headers["Sec-CH-UA-Platform"] = header["sec_ch_ua_platform"]

    return request_headers
