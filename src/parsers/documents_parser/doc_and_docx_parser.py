import logging
import shutil
import subprocess
import sys
from pathlib import Path
from langchain_docling import DoclingLoader
from langchain_core.documents import Document
from src.parsers.constants import _EXPORT_TYPE, _CHUNKER
from src.parsers.entries import DocumentEntry
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

def doc_to_docx(path: str) -> str | None:
    file_path = Path(path)
    output_dir = str(file_path.parent)

    libreoffice_cmd = "soffice" if sys.platform in ["win32", "darwin"] else "libreoffice"
    logger.info("[DOC] Converting %s to DOCX using %s", path, libreoffice_cmd)

    try:
        subprocess.run(
            [libreoffice_cmd, "--headless", "--convert-to", "docx", path, "--outdir", output_dir],
            check=True,
            timeout=10,
        )
        logger.info("[DOC] Conversion successful: %s", file_path.with_suffix(".docx"))
        return str(file_path.with_suffix(".docx"))
    except FileNotFoundError:
        logger.warning("[DOC] LibreOffice not found — will try direct DOCX load for %s", path)
        return None
    except subprocess.CalledProcessError as e:
        logger.error("[DOC] LibreOffice exited with code %d converting %s", e.returncode, path)
        return None
    except subprocess.TimeoutExpired:
        logger.error("[DOC] LibreOffice timed out converting %s", path)
        return None


def process_document(document_entry: DocumentEntry) -> list[Document]:
    path = str(document_entry.local_path)
    tmp_path: str | None = None

    if Path(path).suffix == ".doc":
        converted = doc_to_docx(path)
        if converted is not None:
            path = converted
        else:
            # LibreOffice unavailable — copy to .docx and let DoclingLoader try.
            # Works for OOXML files saved with .doc extension (common on university sites).
            # True binary DOC will fail the load and be caught below.
            tmp_path = path + "x"
            shutil.copy2(path, tmp_path)
            path = tmp_path

    logger.info("[DOC] Loading document: %s", path)
    try:
        loader = DoclingLoader(
            file_path=path,
            export_type=_EXPORT_TYPE,
            chunker=_CHUNKER,
        )
        docs = loader.load()
    except Exception as e:
        logger.warning("[DOC] Could not load %s: %s", path, e)
        docs = []
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    logger.info("[DOC] Loaded %d chunk(s) from %s", len(docs), path)
    apply_document_metadata(docs, document_entry, str(document_entry.local_path))
    return docs
