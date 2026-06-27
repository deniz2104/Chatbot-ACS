import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def pipeline_error(label: str, source: str):
    try:
        yield
    except Exception as e:
        logger.error("[%s] Failed for %s: %s", label, source, e)
