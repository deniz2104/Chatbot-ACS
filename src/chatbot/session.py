import logging
import shutil
from pathlib import Path
from typing import Optional

from src.files_store.init_files import get_chatbot_file_store
from src.utils.singleton import shutdown_all_singletons

logger = logging.getLogger(__name__)

def reset_session(files_store: Optional[str] = None) -> None:
    if files_store is None:
        files_store = get_chatbot_file_store()

    shutdown_all_singletons()
    Path(files_store, "chatbot_output.json").unlink(missing_ok=True)
    shutil.rmtree(Path(f"{files_store}/full"), ignore_errors=True)
    shutil.rmtree(Path(Path(__file__).parent.parent / "models"), ignore_errors=True)
    logger.info("[SESSION] Session reset complete")
