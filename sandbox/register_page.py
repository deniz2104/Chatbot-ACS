import time
import streamlit as st

from sandbox.validate_class import decide_class
from sandbox.constants import _PASSWORD_REQUIREMENTS, _USERNAME_REQUIREMENTS, _CLEAR_DELAY
from sandbox.meeting_requests import meeting_request
from sandbox.utils import elapsed


def render_register() -> None:
    st.title("Register")

    password = password_confirm = ""
    password_valid = False
    now = time.time()

    username = st.text_input("Username", key="reg_username")

    u_placeholder = st.empty()
    if elapsed("u_valid_since") < _CLEAR_DELAY:
        with u_placeholder.container():
            username_valid = meeting_request(username, _USERNAME_REQUIREMENTS)
    else:
        u_placeholder.empty()
        username_valid = meeting_request(username, _USERNAME_REQUIREMENTS, render=False)

    if not username_valid:
        st.session_state.pop("u_valid_since", None)
        st.info("Complete a valid username to unlock the password fields.")
    elif "u_valid_since" not in st.session_state:
        st.session_state.u_valid_since = now

    if username_valid:
        password = st.text_input("Password", type="password", key="reg_password")

        p_placeholder = st.empty()
        if elapsed("p_valid_since") < _CLEAR_DELAY:
            with p_placeholder.container():
                password_valid = meeting_request(password, _PASSWORD_REQUIREMENTS)
        else:
            p_placeholder.empty()
            password_valid = meeting_request(password, _PASSWORD_REQUIREMENTS, render=False)

        if not password_valid:
            st.session_state.pop("p_valid_since", None)
            st.info("Complete a valid password to unlock the confirm password field.")
        elif "p_valid_since" not in st.session_state:
            st.session_state.p_valid_since = now

    if username_valid and password_valid:
        password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

    faculty_year = st.selectbox("Faculty Year", options=["I", "II", "III", "IV"])
    department = st.selectbox("Department", options=["Automatica", "Calculatoare"])
    faculty_class, specialization = decide_class(faculty_year, department)

    if specialization:
        st.info(f"Specialization: **{specialization}**")

    if st.button("Register"):
        if not username or not password or not password_confirm:
            st.error("Fill in all fields.")
            return

        if password != password_confirm:
            st.error("Passwords do not match.")
            return

        # Mock: registration always succeeds
        st.success("Account created. You can now log in.")
        st.session_state.auth_page = "login"
        st.rerun()

    st.divider()

    if st.button("← Back to Login", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()
