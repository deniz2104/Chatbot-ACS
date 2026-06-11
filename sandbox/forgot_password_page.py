import time
import streamlit as st

from sandbox.meeting_requests import meeting_request
from sandbox.constants import _PASSWORD_REQUIREMENTS, _CLEAR_DELAY
from sandbox.utils import elapsed


def render_forgot_password() -> None:
    st.title("Forgot Password")
    password = password_confirm = ""
    password_valid = False
    now = time.time()

    username = st.text_input(
        "Username",
        value=st.session_state.get("fp_username", ""),
        disabled=st.session_state.get("fp_username") is not None,
    )

    if username and not st.session_state.get("fp_username"):
        st.session_state.fp_username = username
        st.session_state.fp_u_valid_since = time.time()
        st.rerun()

    if st.session_state.get("fp_username"):
        u_success_placeholder = st.empty()
        if elapsed("fp_u_valid_since") < _CLEAR_DELAY:
            u_success_placeholder.success("Username exists. Please input a new password.")
            st.rerun()
        else:
            u_success_placeholder.empty()

        password = st.text_input("Password", type="password", key="reg_password")

        p_placeholder = st.empty()
        if elapsed("fp_p_valid_since") < _CLEAR_DELAY:
            with p_placeholder.container():
                password_valid = meeting_request(password, _PASSWORD_REQUIREMENTS)
        else:
            p_placeholder.empty()
            password_valid = meeting_request(password, _PASSWORD_REQUIREMENTS, render=False)

        if not password_valid:
            st.session_state.pop("fp_p_valid_since", None)
            st.info("Complete a valid password to unlock the confirm password field.")
        elif "fp_p_valid_since" not in st.session_state:
            st.session_state.fp_p_valid_since = now

        if password_valid:
            password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

        if st.button("Reset Password"):
            if not password or not password_confirm:
                st.error("Fill in all fields.")
                return

            if password != password_confirm:
                st.error("Passwords do not match.")
                return

            st.success("Password reset successful. You can now log in.")
            st.session_state.pop("fp_username", None)
            st.session_state.auth_page = "login"
            st.rerun()

    st.divider()

    if st.button("← Back to Login", use_container_width=True):
        st.session_state.pop("fp_username", None)
        st.session_state.auth_page = "login"
        st.rerun()
