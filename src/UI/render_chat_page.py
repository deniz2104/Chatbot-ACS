import logging
import streamlit as st
from datetime import datetime, timezone

from src.UI.render_sidebar import render_sidebar
from src.azure.db.load_conversation_messages import load_conversation_messages
from src.ai_prompts.chatbot_responder import get_chatbot_response
from src.ai_prompts.query_rewriter import rewrite_query
from src.vector_database.query import query as handle_query
from src.UI.conversation import create_user_conversation
from src.UI.constants import CONVERSATION_LIFETIME

logger = logging.getLogger(__name__)

_DEPT_LABEL = {
    "Automatica": "Ingineria Sistemelor (IS)",
    "Calculatoare": "Calculatoare și Tehnologia Informației (CTI)",
}

def _build_user_context() -> str:
    user = st.session_state.user
    year = user.get("year", "")
    department = user.get("department", "")
    student_class = user.get("student_class", "")
    dept_label = _DEPT_LABEL.get(department, department)
    return ", ".join(str(p) for p in [f"An {year}" if year else "", dept_label, student_class] if p)

def _render_history() -> None:
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def _get_current_conversation() -> dict | None:
    conversation_id = st.session_state.get("conversation_id")
    if not conversation_id:
        return None
    conversations: list[dict] = st.session_state.get("conversations", [])
    return next((c for c in conversations if c.get("RowKey") == conversation_id), None)

def _sync_messages(connection_string: str) -> None:
    conversation_id = st.session_state.get("conversation_id")
    loaded_id = st.session_state.get("loaded_conversation_id")

    if not conversation_id or conversation_id == loaded_id:
        return

    username = st.session_state.user["RowKey"]
    st.session_state.messages = load_conversation_messages(
        connection_string, username, conversation_id
    )
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.last_sources = []

def _render_sources() -> None:
    sources: list[str] = st.session_state.get("last_sources", [])
    if not sources:
        return
    with st.expander(f"Surse ({len(sources)})", expanded=False):
        for src in sources:
            st.markdown(f"- [{src}]({src})")

def _retrieve_docs(prompt: str, user_context: str) -> list:
    return handle_query(rewrite_query(prompt), user_context=user_context)

def render_chat_page(connection_string: str) -> None:
    render_sidebar(connection_string)
    _sync_messages(connection_string)
    _render_history()
    _render_sources()

    is_waiting = st.session_state.get("is_waiting", False)
    conv = _get_current_conversation()
    if conv:
        created_at_str: str = conv.get("created_at", "")
        is_locked = datetime.now(timezone.utc) - datetime.fromisoformat(created_at_str) > CONVERSATION_LIFETIME
    else:
        is_locked = False

    if is_locked:
        st.caption("Această conversație a expirat. Începe o conversație nouă.")

    if prompt := st.chat_input("Întreabă ceva despre facultate...", disabled=is_waiting or is_locked):
        st.session_state.pending_prompt = prompt
        st.session_state.is_waiting = True
        st.rerun()

    if is_waiting and (prompt := st.session_state.pop("pending_prompt", None)):
        if st.session_state.get("conversation_id") is None:
            create_user_conversation(connection_string)

        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})

        user_context = _build_user_context()
        conv = _get_current_conversation()
        conversation_summary = (conv or {}).get("summary", "")

        with st.spinner("Se caută răspunsul..."):
            docs = _retrieve_docs(prompt, user_context)

        with st.chat_message("assistant"):
            stream = get_chatbot_response(
                prompt, docs, st.session_state.messages,
                user_context=user_context,
                conversation_summary=conversation_summary,
            )
            response = st.write_stream(stream)

        st.session_state.messages.append({"role": "assistant", "content": response})

        st.session_state.last_sources = [
            doc.metadata.get("url") for doc in docs if doc.metadata.get("url")
        ]
        st.session_state.is_waiting = False
        st.rerun()
