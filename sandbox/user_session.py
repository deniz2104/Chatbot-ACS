from datetime import datetime, timezone, timedelta
import streamlit as st

SESSION_LIFETIME: timedelta = timedelta(hours=1)


def _is_session_expired() -> bool:
    login_time: datetime | None = st.session_state.get("login_time")
    if login_time is None:
        return True
    return datetime.now(timezone.utc) - login_time > SESSION_LIFETIME


def verify_session() -> None:
    if st.session_state.user:
        if _is_session_expired():
            st.session_state.clear()
            set_initial_session()
            st.warning("Your session has expired. Please log in again.")
            st.rerun()


def set_initial_session() -> None:
    from sandbox.set_initial_session import set_initial_session as _set
    _set()
