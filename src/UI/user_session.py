from datetime import datetime, timezone
import streamlit as st

from src.UI.constants import SESSION_LIFETIME

def _is_session_expired() -> bool:
    login_time: datetime | None = st.session_state.get("login_time")
    if login_time is None:
        return True
    return datetime.now(timezone.utc) - login_time > SESSION_LIFETIME

def verify_session(connection_string: str) -> None:
    if st.session_state.user:
        if _is_session_expired():
            from src.UI.delete_chatbot_session import delete_session
            delete_session(connection_string)
            st.warning("Your session has expired. Please log in again.")
            st.rerun()
    return
