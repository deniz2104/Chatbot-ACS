import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.scraper.header_builder import BrowserHeader, format_header_for_requests
from src.scraper.ua_rotator import create_browser_header, load_headers_from_json
from src.scraper.http_client import CustomHttpAdapter
from src.scraper.retry import RetryConfig, RetryHandler


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


def _make_headers_pool() -> list[BrowserHeader]:
    return [
        create_browser_header("Mozilla/5.0 Chrome/120.0.0.0", "chrome", "windows"),
    ]


def _ok_response(text: str = "<html>OK</html>") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.ok = True
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


def _fail_response(status_code: int = 500) -> MagicMock:
    import requests as req
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = False
    resp.raise_for_status.side_effect = req.RequestException("fail")
    return resp


class TestGetRandomHeader(unittest.TestCase):

    def test_get_random_header_returns_valid_dict(self):
        from src.scraper.scraper import BrowserHeaderScraper
        scraper = BrowserHeaderScraper(_make_headers_pool())
        header = scraper.get_random_header()
        self.assertIsInstance(header, dict)
        self.assertIn("User-Agent", header)


class TestScrape(unittest.TestCase):

    def _make_scraper(self):
        from src.scraper.scraper import BrowserHeaderScraper
        return BrowserHeaderScraper(_make_headers_pool())

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_scrape_success(self, _mock_sleep):
        scraper = self._make_scraper()
        scraper.session.get = MagicMock(return_value=_ok_response())

        result = scraper.scrape("https://example.com")
        self.assertEqual(result, "<html>OK</html>")

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_scrape_retries_then_succeeds(self, _mock_sleep):
        scraper = self._make_scraper()

        scraper.session.get = MagicMock(
            side_effect=[_fail_response(), _fail_response(), _ok_response("OK")],
        )
        result = scraper.scrape("https://example.com", max_retries=3)
        self.assertEqual(result, "OK")
        self.assertEqual(scraper.session.get.call_count, 3)

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_scrape_gives_up_after_max_retries(self, _mock_sleep):
        scraper = self._make_scraper()

        scraper.session.get = MagicMock(
            side_effect=[_fail_response(), _fail_response(), _fail_response()],
        )
        result = scraper.scrape("https://example.com", max_retries=3)
        self.assertIsNone(result)


class TestRetryHandler(unittest.TestCase):

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_returns_response_on_success(self, _mock_sleep):
        session = MagicMock()
        session.get.return_value = _ok_response("data")

        handler = RetryHandler(RetryConfig(max_retries=3))
        response = handler.execute(session, "https://example.com")
        self.assertIsNotNone(response)
        self.assertEqual(response.text, "data")
        self.assertEqual(session.get.call_count, 1)

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_retries_on_retryable_status(self, _mock_sleep):
        session = MagicMock()
        session.get.side_effect = [_fail_response(503), _ok_response("ok")]

        handler = RetryHandler(RetryConfig(max_retries=3))
        response = handler.execute(session, "https://example.com")
        self.assertIsNotNone(response)
        self.assertEqual(session.get.call_count, 2)

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_returns_none_after_exhausting_retries(self, _mock_sleep):
        session = MagicMock()
        import requests as req
        exc = req.RequestException("timeout")
        session.get.side_effect = exc

        handler = RetryHandler(RetryConfig(max_retries=2))
        response = handler.execute(session, "https://example.com")
        self.assertIsNone(response)
        self.assertEqual(session.get.call_count, 2)

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_on_retry_callback_is_called(self, _mock_sleep):
        session = MagicMock()
        session.get.side_effect = [_fail_response(500), _ok_response("ok")]

        callback = MagicMock(return_value={"X-Custom": "new"})
        handler = RetryHandler(RetryConfig(max_retries=3))
        handler.execute(session, "https://example.com", on_retry=callback)
        callback.assert_called_once()

    @patch("src.scraper.retry.time.sleep", return_value=None)
    def test_backoff_delay_increases(self, mock_sleep):
        session = MagicMock()
        import requests as req
        session.get.side_effect = req.RequestException("fail")

        handler = RetryHandler(RetryConfig(max_retries=3, backoff_factor=1.0))
        handler.execute(session, "https://example.com")

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # backoff_factor * 2^attempt: 1*1=1, 1*2=2
        self.assertEqual(delays, [1.0, 2.0])

    def test_default_retryable_status_codes(self):
        config = RetryConfig()
        self.assertEqual(config.retryable_status_codes, {429, 500, 502, 503, 504})

    def test_custom_retryable_status_codes(self):
        config = RetryConfig(retryable_status_codes={408, 429})
        self.assertEqual(config.retryable_status_codes, {408, 429})


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


class TestCustomHttpAdapter(unittest.TestCase):

    @patch("src.scraper.http_client.create_urllib3_context")
    @patch("requests.adapters.HTTPAdapter.init_poolmanager")
    def test_custom_http_adapter_sets_ssl_context(self, mock_super_init, mock_ctx_factory):
        mock_ctx = MagicMock()
        mock_ctx_factory.return_value = mock_ctx

        adapter = CustomHttpAdapter()
        adapter.init_poolmanager(1, 2, key="value")

        mock_ctx.set_ciphers.assert_called_with("DEFAULT@SECLEVEL=1")
        self.assertFalse(mock_ctx.check_hostname)
        _, kwargs = mock_super_init.call_args
        self.assertIs(kwargs["ssl_context"], mock_ctx)


if __name__ == "__main__":
    unittest.main()
