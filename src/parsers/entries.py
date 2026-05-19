from dataclasses import dataclass
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"

@dataclass
class BasicEntry:
    url_slug: str
    title: str

@dataclass
class PageEntry(BasicEntry):
    text: str
    tables: str

@dataclass
class DocumentEntry(BasicEntry):
    local_path: str

