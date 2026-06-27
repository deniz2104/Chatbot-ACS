import time
from collections.abc import Callable

import streamlit as st

from src.azure.acs.otp import verify_otp, _OTP_LENGTH
from src.UI.constants import _CLEAR_DELAY


def render_otp_screen(
    *,
    username: str,
    email: str,
    sent_at_key: str,
    description: str,
    verify_label: str,
    back_label: str,
    on_back: Callable[[], None],
    resend_fn: Callable[[], bool],
) -> bool:
    
    placeholder = st.empty()
    sent_at = st.session_state.get(sent_at_key, 0)
    if time.time() - sent_at < _CLEAR_DELAY:
        placeholder.success(f"A {description} code was sent to **{email}**.")
        st.rerun()
    else:
        placeholder.empty()

    st.info(f"A {_OTP_LENGTH}-digit {description} code was sent to **{email}**.")
    otp_input = st.text_input("Enter code", max_chars=_OTP_LENGTH, key=f"otp_input_{sent_at_key}")

    verified = False
    if st.button(verify_label, disabled=len(otp_input) != _OTP_LENGTH, key=f"verify_{sent_at_key}"):
        if verify_otp(username, otp_input):
            verified = True
        else:
            st.error("Invalid or expired code.")

    if st.button("Resend Code", key=f"resend_{sent_at_key}"):
        if resend_fn():
            st.session_state[sent_at_key] = time.time()
        else:
            st.error("Failed to resend the code. Please try again.")

    st.divider()
    if st.button(back_label, use_container_width=True, key=f"back_{sent_at_key}"):
        on_back()

    return verified
