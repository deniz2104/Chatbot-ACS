import streamlit as st


def set_initial_session() -> None:
    defaults: dict = {
        "user": None,
        "login_time": None,
        "auth_page": "login",
        "show_sources": False,
        "last_sources": [],
        "messages": [],
        "conversation_id": None,
        "loaded_conversation_id": None,
        "conversations": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
