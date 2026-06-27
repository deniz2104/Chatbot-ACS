import logging
from collections.abc import Generator
from contextlib import contextmanager

import anthropic

logger = logging.getLogger(__name__)


@contextmanager
def anthropic_call(tag: str) -> Generator[None, None, None]:
    try:
        yield
    except anthropic.AuthenticationError:
        logger.error("[%s] Invalid API key", tag)
        raise
    except anthropic.RateLimitError:
        logger.warning("[%s] Rate limit hit", tag)
    except anthropic.APIConnectionError:
        logger.warning("[%s] API connection failed", tag)
    except anthropic.APIStatusError as e:
        logger.warning("[%s] API error %s", tag, e.status_code)


def stream_anthropic_call(
    stream_context,
    tag: str,
    rate_limit_msg: str = "Sorry, the server is temporarily overloaded. Please try again.",
    connection_msg: str = "Sorry, I cannot connect to the server. Please check your internet connection.",
    api_error_msg: str = "Sorry, an error occurred. Please try again.",
) -> Generator[str, None, None]:
    try:
        with stream_context as stream:
            yield from stream.text_stream
    except anthropic.AuthenticationError:
        logger.error("[%s] Invalid API key", tag)
        raise
    except anthropic.RateLimitError:
        logger.warning("[%s] Rate limit hit", tag)
        yield rate_limit_msg
    except anthropic.APIConnectionError:
        logger.warning("[%s] API connection failed", tag)
        yield connection_msg
    except anthropic.APIStatusError as e:
        logger.warning("[%s] API error %s", tag, e.status_code)
        yield api_error_msg
