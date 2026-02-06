import logging
from fake_useragent import UserAgent

logging.getLogger("fake_useragent").setLevel(logging.CRITICAL)

_ua = UserAgent(
    os=["windows", "macos", "linux"],
    browsers=["chrome", "firefox", "safari"],
)

def generate_random_ua() -> dict[str, str]:
    return {"User-Agent": _ua.random}
