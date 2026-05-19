import logging
import subprocess
import sys
from pathlib import Path
from langchain_docling import DoclingLoader
from langchain_core.documents import Document
from src.parsers.constants import _EXPORT_TYPE, _CHUNKER
from src.parsers.entries import DocumentEntry
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

def doc_to_docx(path: str) -> str:
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
    except FileNotFoundError:
        logger.error("[DOC] LibreOffice not found — is soffice/libreoffice installed?")
        raise RuntimeError("LibreOffice not found — install soffice or libreoffice")
    except subprocess.CalledProcessError as e:
        logger.error("[DOC] LibreOffice exited with code %d converting %s", e.returncode, path)
        raise RuntimeError(f"LibreOffice conversion failed for {path}")
    except subprocess.TimeoutExpired:
        logger.error("[DOC] LibreOffice timed out converting %s", path)
        raise RuntimeError(f"LibreOffice timed out converting {path}")

    return str(file_path.with_suffix(".docx"))

def process_document(document_entry: DocumentEntry) -> list[Document]:
    path = document_entry.local_path
    if path.endswith(".doc"):
        path = doc_to_docx(path)

    logger.info("[DOC] Loading document: %s", path)
    loader = DoclingLoader(
        file_path=path,
        export_type=_EXPORT_TYPE,
        chunker=_CHUNKER,
    )
    docs = loader.load()
    logger.info("[DOC] Loaded %d chunk(s) from %s", len(docs), path)

    apply_document_metadata(docs, document_entry, path)
    return docs