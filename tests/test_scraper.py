import json
import os
import tempfile
import unittest

from src.token_scraper.header_builder import BrowserHeader, format_header_for_requests
from src.token_scraper.ua_rotator import create_browser_header, load_headers_from_json


class TestBrowserHeader(unittest.TestCase):

    def test_browser_header_has_all_keys(self):
        expected_keys = {
            "user_agent", "accept", "accept_language", "accept_encoding",
            "sec_ch_ua", "sec_ch_ua_mobile", "sec_ch_ua_platform",
            "sec_fetch_dest", "sec_fetch_mode", "sec_fetch_site",
            "sec_fetch_user", "upgrade_insecure_requests",
            "cache_control", "pragma", "browser", "os", "timestamp",
        }
        self.assertEqual(set(BrowserHeader.__annotations__.keys()), expected_keys)

    def test_format_header_chrome_includes_sec_ch_ua(self):
        header = create_browser_header(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "chrome",
            "windows",
        )
        formatted = format_header_for_requests(header)
        self.assertIn("Sec-CH-UA", formatted)
        self.assertIn("Sec-CH-UA-Mobile", formatted)
        self.assertIn("Sec-CH-UA-Platform", formatted)

    def test_format_header_firefox_excludes_sec_ch_ua(self):
        header = create_browser_header(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
            "firefox",
            "windows",
        )
        formatted = format_header_for_requests(header)
        self.assertNotIn("Sec-CH-UA", formatted)
        self.assertNotIn("Sec-CH-UA-Mobile", formatted)
        self.assertNotIn("Sec-CH-UA-Platform", formatted)


class TestLoadHeadersFromJson(unittest.TestCase):

    def test_load_headers_from_json_returns_list(self):
        headers = [
            create_browser_header("Mozilla/5.0 Chrome/120.0.0.0", "chrome", "windows"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(headers, f)
            tmp_path = f.name

        try:
            loaded = load_headers_from_json(tmp_path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["browser"], "chrome")
            self.assertEqual(loaded[0]["os"], "windows")
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
