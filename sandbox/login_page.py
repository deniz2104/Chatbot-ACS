import streamlit as st
from datetime import datetime, timezone

from sandbox.conversation import create_user_conversation

def render_columns(column: st.container, text: str, redirect_page: str) -> None:
    with column:
        if st.button(text, use_container_width=True):
            st.session_state.auth_page = redirect_page
            st.rerun()

def render_login() -> None:
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Fill in all fields.")
            return

        # Mock: accept any non-empty credentials
        st.session_state.user = {"RowKey": username, "username": username}
        st.session_state.login_time = datetime.now(timezone.utc)
        create_user_conversation()
        st.rerun()

    st.divider()

    col1, col2 = st.columns(2)
    render_columns(col1, "Register", "register")
    render_columns(col2, "Forgot Password", "forgot")