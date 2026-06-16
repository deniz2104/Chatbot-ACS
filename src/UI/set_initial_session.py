import streamlit as st
import threading
from src.azure.db.table_client import init_tables

def set_initial_session(connection_string: str) -> None:
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

    if not st.session_state.get("_tables_initialized"):
        threading.Thread(target=init_tables, args=(connection_string,), daemon=True).start()
        st.session_state._tables_initialized = True
