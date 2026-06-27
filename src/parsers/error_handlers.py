import logging
import subprocess
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def libreoffice_errors(path: str):
    try:
        yield
    except FileNotFoundError:
        logger.warning("[DOC] LibreOffice not found — will try direct DOCX load for %s", path)
    except subprocess.CalledProcessError as e:
        logger.error("[DOC] LibreOffice exited with code %d converting %s", e.returncode, path)
    except subprocess.TimeoutExpired:
        logger.error("[DOC] LibreOffice timed out converting %s", path)


@contextmanager
def parse_error(label: str, path: str):
    try:
        yield
    except Exception as e:
        logger.error("[%s] Failed for %s: %s", label, path, e)
