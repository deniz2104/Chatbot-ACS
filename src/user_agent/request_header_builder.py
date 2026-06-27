import random

from src.user_agent.user_agent import create_browser_header
from src.user_agent.constants import ACCEPT_LANGUAGES, STATIC_HEADERS

def build_request_headers() -> dict[str, str]:
    header = create_browser_header()

    headers = {
        **STATIC_HEADERS,
        "accept-language": random.choice(ACCEPT_LANGUAGES),
        **header.headers.get(),
    }

    return headers
