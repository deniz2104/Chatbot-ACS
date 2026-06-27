import time
import streamlit as st

from src.azure.db.auth.verify_user import username_exists, email_matches
from src.azure.db.auth.change_password import update_password
from src.UI.render.render_otp_screen import render_otp_screen
from src.UI.constants import _PASSWORD_REQUIREMENTS, _EMAIL_REQUIREMENTS
from src.UI.utils import timing_placeholder, validate_field, navigate_to, send_otp, autorefresh_if_validating


def _clear_fp_state() -> None:
    for key in ("fp_username", "fp_email", "fp_u_valid_since", "fp_otp_verified", "fp_p_valid_since"):
        st.session_state.pop(key, None)


def _back_to_login() -> None:
    _clear_fp_state()
    navigate_to("login")


def render_forgot_password(connection_string: str) -> None:
    st.title("Forgot Password")
    now = time.time()

    if not st.session_state.get("fp_username"):
        username = st.text_input("Username")
        email = st.text_input("Email")

        e_placeholder = st.empty()
        email_valid = timing_placeholder(e_placeholder, "fp_e_valid_since", email, _EMAIL_REQUIREMENTS)
        validate_field(email_valid, "fp_e_valid_since", "Enter a valid email address.", now)

        autorefresh_if_validating(["fp_e_valid_since"], now)

        if st.button("Send Reset Code", disabled=not (username and email_valid)):
            if not username_exists(connection_string, username):
                st.error("Username does not exist.")
            elif not email_matches(connection_string, username, email):
                st.error("Email does not match the registered address.")
            else:
                normalized = email.strip().lower()
                st.session_state.fp_username = username
                st.session_state.fp_email = normalized
                if send_otp(username, normalized, reason="password reset"):
                    st.session_state.fp_u_valid_since = time.time()
                    st.rerun()
                else:
                    st.session_state.pop("fp_username", None)
                    st.session_state.pop("fp_email", None)

        st.divider()
        if st.button("← Back to Login", use_container_width=True):
            _back_to_login()
        return

    if not st.session_state.get("fp_otp_verified"):
        verified = render_otp_screen(
            username=st.session_state.fp_username,
            email=st.session_state.fp_email,
            sent_at_key="fp_u_valid_since",
            description="reset",
            verify_label="Verify Code",
            back_label="← Back to Login",
            on_back=_back_to_login,
            resend_fn=lambda: send_otp(
                st.session_state.fp_username,
                st.session_state.fp_email,
                reason="password reset",
            ),
        )
        if verified:
            st.session_state.fp_otp_verified = True
            st.rerun()
        return

    password = password_confirm = ""
    password_valid = False

    st.success("Identity verified. Please set a new password.")
    password = st.text_input("New Password", type="password", key="reg_password")

    p_placeholder = st.empty()
    password_valid = timing_placeholder(p_placeholder, "fp_p_valid_since", password, _PASSWORD_REQUIREMENTS)
    validate_field(password_valid, "fp_p_valid_since", "Complete a valid password to unlock the confirm field.", now)

    autorefresh_if_validating(["fp_p_valid_since"], now)

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
        _back_to_login()

    st.divider()
    if st.button("← Back to Login", use_container_width=True):
        _back_to_login()
