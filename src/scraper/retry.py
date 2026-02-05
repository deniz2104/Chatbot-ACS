import time
from typing import Callable, Optional
from dataclasses import dataclass, field

import requests


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_factor: float = 0.5
    timeout: int = 10
    retryable_status_codes: set[int] = field(
        default_factory=lambda: {429, 500, 502, 503, 504},
    )

class RetryHandler:
    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        self.config = config or RetryConfig()

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code in self.config.retryable_status_codes

    def _backoff_delay(self, attempt: int) -> float:
        return self.config.backoff_factor * (2 ** attempt)

    def execute(
        self,
        session: requests.Session,
        url: str,
        headers: Optional[dict[str, str]] = None,
        on_retry: Optional[Callable] = None,
    ) -> Optional[requests.Response]:
        cfg = self.config

        for attempt in range(cfg.max_retries):
            try:
                response = session.get(
                    url,
                    headers=headers,
                    timeout=cfg.timeout,
                    verify=False,
                )

                if response.ok:
                    return response

                if self._should_retry_status(response.status_code):
                    print(f"Retryable status code {response.status_code} on attempt {attempt + 1}")
                    if attempt < cfg.max_retries - 1:
                        if on_retry:
                            headers = on_retry(attempt, response) or headers
                        time.sleep(self._backoff_delay(attempt))
                        continue

                response.raise_for_status()

            except requests.RequestException:
                print(f"Request failed on attempt {attempt + 1}")
                if attempt == cfg.max_retries - 1:
                    return None
                if on_retry:
                    headers = on_retry(attempt, None) or headers
                time.sleep(self._backoff_delay(attempt))

        return None
