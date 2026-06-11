import streamlit as st
from datetime import datetime, timezone

from src.DB.login_user import login_user
from src.UI.conversation import create_user_conversation

def _render_columns(column, text: str, redirect_page: str) -> None:
    with column:
        if st.button(text, use_container_width=True):
            st.session_state.auth_page = redirect_page
            st.rerun()

def render_login(connection_string: str) -> None:
    st.title("Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not username or not password:
            st.error("Fill in all fields.")
            return

        user = login_user(connection_string, username, password)
        if user is None:
            st.error("Invalid username or password.")
            return

        st.session_state.user = user
        st.session_state.login_time = datetime.now(timezone.utc)
        create_user_conversation(connection_string)
        st.rerun()

    st.divider()

    col1, col2 = st.columns(2)
    _render_columns(col1, "Register", "register")
    _render_columns(col2, "Forgot Password", "forgot")
