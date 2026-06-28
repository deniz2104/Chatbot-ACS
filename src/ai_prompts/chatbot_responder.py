import logging
from collections.abc import Generator

from langchain_core.documents import Document

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL, _NUMBER_OF_CONVERSATIONS
from src.ai_prompts.error_handlers import stream_anthropic_call
from src.ai_prompts.utils import make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ești un asistent virtual al Facultății de Automatică și Calculatoare (ACS) "
    "din cadrul Universității Politehnica București.\n\n"
    "Răspunzi întrebărilor studenților cu privire la facultate, programe de studiu, examene, "
    "regulamente, orare și alte informații academice.\n\n"
    "Folosește exclusiv informațiile din contextul furnizat. "
    "Dacă găsești informații relevante, chiar și parțiale sau dintr-un singur document, "
    "prezintă-le clar și complet. "
    "Răspunde cu 'nu am informații disponibile' doar dacă absolut niciun document din context "
    "nu conține date utile pentru întrebare.\n\n"
    "Răspunde întotdeauna în română cu diacritice corecte."
)


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        f"[Sursă {i + 1}]: {doc.page_content}"
        for i, doc in enumerate(docs)
    )

def get_chatbot_response(
    user_query: str,
    docs: list[Document],
    history: list[dict],
    user_context: str = "",
    conversation_summary: str = "",
) -> Generator[str, None, None]:
    
    context = _format_docs(docs)
    user_content = (
        f"{user_query}\n\nInformații relevante din surse:\n{context}"
        if context else user_query
    )

    past_turns = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-_NUMBER_OF_CONVERSATIONS:-1]
    ]
    llm_messages = past_turns + [{"role": "user", "content": user_content}]
    system_prompt = _SYSTEM_PROMPT
    system_prompt += f"\n\nProfilul studentului: {user_context}" if user_context else ""
    system_prompt += f"\n\nRezumatul conversației curente: {conversation_summary}" if conversation_summary else ""

    template = make_ai_template(
        system_prompt=system_prompt,
        tokens=1024,
        messages=llm_messages,
        model=_SONNET_MODEL,
    )

    yield from stream_anthropic_call(_CLIENT.messages.stream(**template.to_dict()), "CHATBOT")
