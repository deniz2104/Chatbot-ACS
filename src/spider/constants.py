import re

EXTENSIONS = frozenset((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"))
IGNORED_HREF_PREFIXES = ("#", "javascript:", "mailto:", "tel:", "ftp:", "data:", "file:")
PAGINATION_PATTERN = re.compile(r'/page/\d+/?$|[?&]paged?=\d+|[?&]page=\d+')
REDIS_KEYS = ("link_website_crawler:dupefilter", "link_website_crawler:requests")
WEBSITES = [
    "https://acs.pub.ro",
    "https://precis.upb.ro",
    "https://aii.pub.ro",
    "https://cs.pub.ro",
]