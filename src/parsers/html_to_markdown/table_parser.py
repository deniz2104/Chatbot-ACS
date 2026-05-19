import logging

import bs4
import scrapy
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

def _is_meaningful_table(tag: bs4.Tag) -> bool:
    cells = tag.find_all(["td", "th"])
    non_empty = [c for c in cells if c.get_text(strip=True)]
    return len(non_empty) >= 2

def select_tables_from_plain_html(response: scrapy.http.Response) -> list[str]:
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    all_tables = soup.find_all("table")
    result = [
        str(t) for t in all_tables
        if t.find_parent("table") is None and _is_meaningful_table(t)
    ]
    logger.debug(
        "[TABLES] %s — found %d table(s), kept %d meaningful",
        response.url, len(all_tables), len(result),
    )
    return result


def tables_to_markdown(html_tables: list[str]) -> list[str]:
    if not html_tables:
        return []

    return [md(t, heading_style="ATX").strip() for t in html_tables]