DENY_PATTERNS = (r'ajax', r'/en/', r'\?')
DOCUMENT_EXTENSIONS = r"\.(?:pdf|xls|xlsx|docx|doc)(?:[?#][^/]*)?$"

def build_year_deny_pattern(min_year: int) -> str:
    decade = min_year % 100 // 10
    parts = [r"19\d{2}"]
    parts += [f"20{d}\\d" for d in range(0, decade)]
    if min_year % 10 > 0:
        parts.append(f"20{decade}[0-{min_year % 10 - 1}]")
    return "|".join(parts)

