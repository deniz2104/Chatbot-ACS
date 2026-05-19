import logging
import shutil
from pathlib import Path

from src.chatbot.category_loader import invalidate_categories_cache
from src.chatbot.url_loader import invalidate_urls_cache
from src.vector_database.vector_db import delete_current, delete_previous
from src.vector_database.query import shutdown_query

logger = logging.getLogger(__name__)

## e de verificat

def reset_session(files_store: str) -> None:
    invalidate_categories_cache()
    invalidate_urls_cache()
    delete_current()
    delete_previous()
    shutdown_query()
    Path(files_store, "chatbot_output.json").unlink(missing_ok=True)
    shutil.rmtree(Path(f"{files_store}/full"), ignore_errors=True)
    logger.info("[SESSION] Session reset complete")
