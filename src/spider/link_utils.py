DENY_PATTERNS = (r'ajax', r'/en/')
QUERY_ALLOW_DOMAINS = frozenset({'acs.wiki.upb.ro'})
WIKI_ACTION_DENY = r'[?&]do=(?:login|admin|media|edit|revisions|diff|search|backlink|recent|register)(?:&|$)'
DOCUMENT_EXTENSIONS = r"\.(?:pdf|xls|xlsx|docx|doc)(?:[?#][^/]*)?$"

def build_year_deny_pattern(min_year: int) -> str:
    decade = min_year % 100 // 10
    parts = [r"19\d{2}"]
    parts += [f"20{d}\\d" for d in range(0, decade)]
    if min_year % 10 > 0:
        parts.append(f"20{decade}[0-{min_year % 10 - 1}]")
    return "|".join(parts)

