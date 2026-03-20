import re
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EXTENSIONS : set = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
EXT_PATTERN = r"(?i)(" + "|".join(re.escape(e) for e in EXTENSIONS) + r")(\?.*)?$"
REDIS_KEYS : tuple = ("link_website_crawler:dupefilter", "link_website_crawler:requests")
MIN_YEAR = datetime.now().year - int(os.environ.get("YEAR_LOOKBACK", "2"))
DENY_PATTERNS = (r'ajax', r'/en/', r'\?')
WEBSITES : list[dict] = [
    {"url": "https://acs.pub.ro", "has_sitemap": False},
    {"url": "https://precis.upb.ro", "has_sitemap": True},
    {"url": "https://aii.pub.ro", "has_sitemap": True},
    {"url": "https://cs.pub.ro", "has_sitemap": False},
    {"url": "https://aimas.cs.pub.ro", "has_sitemap": True},
    {"url": "https://ocw.cs.pub.ro", "has_sitemap": False},
    {"url": "https://acse.pub.ro", "has_sitemap": False},
    #{"url": "http://acs.wiki.upb.ro", "has_sitemap": False},
    #{"url": "https://www.upb.ro", "has_sitemap": False},
]