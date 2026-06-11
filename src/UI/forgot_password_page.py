import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.DB.verify_user import username_exists
from src.DB.change_password import update_password
from src.UI.constants import _PASSWORD_REQUIREMENTS, _CLEAR_DELAY
from src.UI.utils import timing_placeholder, validate_field, elapsed

def render_forgot_password(connection_string: str) -> None:
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
        if username_exists(connection_string, username):
            st.session_state.fp_username = username
            st.session_state.fp_u_valid_since = time.time()
            st.rerun()
        else:
            st.error("Username does not exist.")

    if st.session_state.get("fp_username"):
        u_success_placeholder = st.empty()
        if elapsed("fp_u_valid_since") < _CLEAR_DELAY:
            u_success_placeholder.success("Username exists. Please input a new password.")
            st.rerun()
        else:
            u_success_placeholder.empty()

        password = st.text_input("Password", type="password", key="reg_password")

        p_placeholder = st.empty()
        password_valid = timing_placeholder(p_placeholder, "fp_p_valid_since", password, _PASSWORD_REQUIREMENTS)
        validate_field(password_valid, "fp_p_valid_since", "Complete a valid password to unlock the confirm password field.", now)

        if st.session_state.get("fp_p_valid_since") and now - st.session_state["fp_p_valid_since"] < _CLEAR_DELAY:
            st_autorefresh(interval=500, key="req_autorefresh")

        if password_valid:
            password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

        if st.button("Reset Password"):
            if not password or not password_confirm:
                st.error("Fill in all fields.")
                return

            if password != password_confirm:
                st.error("Passwords do not match.")
                return

            update_password(connection_string, st.session_state.fp_username, password_confirm)
            st.success("Password reset successful. You can now log in.")
            st.session_state.pop("fp_username", None)
            st.session_state.auth_page = "login"
            st.rerun()

    st.divider()

    if st.button("← Back to Login", use_container_width=True):
        st.session_state.pop("fp_username", None)
        st.session_state.auth_page = "login"
        st.rerun()
