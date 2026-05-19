import logging

import scrapy
import trafilatura

logger = logging.getLogger(__name__)

def parse_content(response: scrapy.http.Response, output_format: str = "markdown") -> str:
    result = trafilatura.extract(
        response.text,
        include_comments=False,
        output_format=output_format,
        include_tables=False,
        include_formatting=True,
        include_links=False,
        deduplicate=True,
        favor_precision=True,
    )
    if result is None:
        logger.debug("[PARSER] Trafilatura returned no content for %s", response.url)
        
    return result or ""