import time

import streamlit as st
from sandbox.render_sidebar import render_sidebar
from sandbox.conversation import load_conversation_messages

_MOCK_RESPONSES = [
    "Aceasta este un răspuns demonstrativ. Funcționalitatea AI nu este activă în modul sandbox.",
    "Îți pot oferi informații despre orar, examene, burse și regulamentele facultății.",
    "Secretariatul facultății este disponibil luni–vineri, între 09:00 și 13:00.",
    "Poți găsi toate informațiile despre cursuri pe platforma Moodle a facultății.",
    "Sesiunea de iarnă 2025 începe pe 20 ianuarie. Mai ai nevoie de alte detalii?",
]

_response_index = [0]


def _get_mock_response() -> str:
    idx = _response_index[0] % len(_MOCK_RESPONSES)
    _response_index[0] += 1
    return _MOCK_RESPONSES[idx]


def _sync_messages() -> None:
    conversation_id = st.session_state.get("conversation_id")
    loaded_id = st.session_state.get("loaded_conversation_id")

    if not conversation_id or conversation_id == loaded_id:
        return

    st.session_state.messages = load_conversation_messages(conversation_id)
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.last_sources = []
    st.session_state.show_sources = False


def _render_sources() -> None:
    if not st.session_state.get("show_sources"):
        return
    sources: list[str] = st.session_state.get("last_sources", [])
    if not sources:
        return
    with st.expander("Surse", expanded=False):
        for src in sources:
            if src:
                st.markdown(f"- {src}")


def render_chat_page() -> None:
    render_sidebar()
    _sync_messages()

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
            time.sleep(1.5)
            response = _get_mock_response()

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.session_state.show_sources = False
        st.session_state.is_waiting = False
        st.rerun()
