import logging

import streamlit as st

from src.UI.render_sidebar import render_sidebar
from src.azure.db.load_conversation_messages import load_conversation_messages
from src.ai_prompts.chatbot_responder import get_chatbot_response
from src.ai_prompts.query_rewriter import rewrite_query
from src.vector_database.query import query as handle_query

logger = logging.getLogger(__name__)


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


def render_chat_page(connection_string: str) -> None:
    render_sidebar(connection_string)
    _sync_messages(connection_string)

    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    _render_sources()

    is_waiting = st.session_state.get("is_waiting", False)

    if prompt := st.chat_input("Întreabă ceva despre facultate...", disabled=is_waiting):
        st.session_state.pending_prompt = prompt
        st.session_state.is_waiting = True
        st.rerun()

    if is_waiting and (prompt := st.session_state.pop("pending_prompt", None)):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Se caută răspunsul..."):
            try:
                docs = handle_query(rewrite_query(prompt))
            except Exception:
                logger.exception("[CHAT] Vector DB query failed")
                docs = []

            response = get_chatbot_response(prompt, docs, st.session_state.messages)

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.session_state.last_sources = [
            doc.metadata.get("url") for doc in docs if doc.metadata.get("url")
        ]
        st.session_state.is_waiting = False

        st.rerun()
