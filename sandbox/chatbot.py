import os
import anthropic

_SYSTEM_PROMPT = (
    "You are a virtual assistant for the Faculty of Automation and Computer Science (ACS) "
    "at Politehnica University of Bucharest.\n\n"
    "You answer student questions about the faculty, study programs, exams, "
    "regulations, timetables, and other academic information.\n\n"
    "If you do not have specific information to answer the question, say so clearly "
    "and suggest the student contact the faculty secretariat or check the official website.\n\n"
    "Always respond in Romanian with correct diacritics."
)

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1024
_HISTORY_LIMIT = 20


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Export it before running the sandbox."
        )
    return anthropic.Anthropic(api_key=api_key)


def get_response(user_query: str, history: list[dict]) -> str:
    client = _get_client()

    messages = []
    for msg in history[-_HISTORY_LIMIT:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_query})

    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=0.0,
            system=_SYSTEM_PROMPT,
            messages=messages,
        )
        return next(
            (b.text for b in response.content if b.type == "text"), ""
        ).strip()
    except anthropic.AuthenticationError:
        return "Eroare: cheia API este invalidă. Verifică variabila de mediu ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return "Serverul este supraîncărcat momentan. Încearcă din nou."
    except anthropic.APIConnectionError:
        return "Nu mă pot conecta la server. Verifică conexiunea la internet."
    except anthropic.APIStatusError as e:
        return f"Eroare API ({e.status_code}). Încearcă din nou."
