import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from collections.abc import Callable

from src.UI.utils import timing_placeholder, validate_field
from src.UI.validate_class import decide_class
from src.azure.db.register_user import register_user
from src.UI.constants import _YEAR_TO_INT, _PASSWORD_REQUIREMENTS, _USERNAME_REQUIREMENTS, _CLEAR_DELAY, _NAME_REQUIREMENTS

def _render_name_requirements(text_input: str, key: str, informative_message: str, time: float, requirements: list[tuple[str, Callable]] = _NAME_REQUIREMENTS) -> tuple[str, bool]:
    name = st.text_input(text_input, key=key)
    placeholder = st.empty()
    name_valid = timing_placeholder(placeholder, f"{key}_valid_since", name, requirements)
    validate_field(name_valid, f"{key}_valid_since", informative_message, time)
    return name, name_valid

def render_register(connection_string: str) -> None:
    st.title("Register")

    password = password_confirm = ""
    password_valid = False
    first_name = last_name = ""
    first_name_valid = last_name_valid = False
    now = time.time()

    username = st.text_input("Username", key="reg_username")

    u_placeholder = st.empty()
    username_valid = timing_placeholder(u_placeholder, "u_valid_since", username, _USERNAME_REQUIREMENTS)
    validate_field(username_valid, "u_valid_since", "Complete a valid username to unlock the password field.", now)

    if username_valid:
        password = st.text_input("Password", type="password", key="reg_password")

        p_placeholder = st.empty()
        password_valid = timing_placeholder(p_placeholder, "p_valid_since", password, _PASSWORD_REQUIREMENTS)
        validate_field(password_valid, "p_valid_since", "Complete a valid password to unlock the confirm password field.", now)

    if username_valid and password_valid:
        password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

    if password_confirm:
        passwords_match = password == password_confirm
        if not passwords_match:
            st.error("Passwords do not match.")
        else:
            st.success("Passwords match.")
            first_name, first_name_valid = _render_name_requirements("First Name", "reg_first_name", "Complete a valid first name.", now)
            last_name, last_name_valid = _render_name_requirements("Last Name", "reg_last_name", "Complete a valid last name.", now)

    if any(st.session_state.get(k) and now - st.session_state[k] < _CLEAR_DELAY
           for k in ("u_valid_since", "p_valid_since", "reg_first_name_valid_since", "reg_last_name_valid_since")):
        st_autorefresh(interval=500, key="req_autorefresh")

    faculty_year = st.selectbox("Faculty Year", options=["I", "II", "III", "IV"])
    department = st.selectbox("Department", options=["Automatica", "Calculatoare"])
    faculty_class, specialization = decide_class(faculty_year, department)

    if specialization:
        st.info(f"Specialization: **{specialization}**")

    all_valid = username_valid and password_valid and first_name_valid and last_name_valid

    if st.button("Register", disabled=not all_valid):
        if not password_confirm:
            st.error("Fill in all fields.")
            return

        if password != password_confirm:
            st.error("Passwords do not match.")
            return

        success = register_user(
            connection_string, username, first_name, last_name, password,
            _YEAR_TO_INT[faculty_year], department, faculty_class
        )
        if not success:
            st.error("Username already exists.")
            return

        st.success("Account created. You can now log in.")
        st.session_state.auth_page = "login"
        st.rerun()

    st.divider()

    if st.button("← Back to Login", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()
