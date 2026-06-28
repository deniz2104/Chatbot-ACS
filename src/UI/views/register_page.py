import time
import streamlit as st
from collections.abc import Callable

from src.UI.utils import timing_placeholder, validate_field, navigate_to, send_otp, autorefresh_if_validating
from src.UI.validate_class import decide_class
from src.UI.render.render_otp_screen import render_otp_screen
from src.azure.db.auth.register_user import register_user
from src.azure.db.auth.verify_user import username_exists, email_exists
from src.UI.constants import (
    _YEAR_TO_INT, _PASSWORD_REQUIREMENTS, _USERNAME_REQUIREMENTS,
    _NAME_REQUIREMENTS, _EMAIL_REQUIREMENTS,
)


def _clear_reg_state() -> None:
    for key in ("reg_pending", "reg_otp_sent_at"):
        st.session_state.pop(key, None)


def _render_name_field(
    label: str,
    key: str,
    hint: str,
    now: float,
    prefill: str = "",
    requirements: list[tuple[str, Callable]] = _NAME_REQUIREMENTS,
) -> tuple[str, bool]:
    if prefill and key not in st.session_state:
        st.session_state[key] = prefill
    value = st.text_input(label, key=key)
    placeholder = st.empty()
    valid = timing_placeholder(placeholder, f"{key}_valid_since", value, requirements)
    validate_field(valid, f"{key}_valid_since", hint, now)
    return value, valid


def _render_form_upb(connection_string: str, upb: dict) -> None:
    """Registration form for users arriving via UPB SSO — username and email are locked."""
    st.title("Înregistrare")
    st.info(
        f"Identitate UPB confirmată. Username-ul și adresa de email au fost preluate automat "
        f"și nu pot fi modificate."
    )
    now = time.time()

    username = upb["username"]
    email = upb["email"]

    st.text_input("Username", value=username, disabled=True)
    st.text_input("Email", value=email, disabled=True)

    password = st.text_input("Password", type="password", key="reg_password")
    p_placeholder = st.empty()
    password_valid = timing_placeholder(p_placeholder, "p_valid_since", password, _PASSWORD_REQUIREMENTS)
    validate_field(password_valid, "p_valid_since", "Completează o parolă validă pentru a debloca câmpul de confirmare.", now)

    password_confirm = ""
    if password_valid:
        password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

    first_name = last_name = ""
    first_name_valid = last_name_valid = False

    if password_confirm:
        if password != password_confirm:
            st.error("Parolele nu coincid.")
        else:
            st.success("Parolele coincid.")
            first_name, first_name_valid = _render_name_field(
                "Prenume", "reg_first_name", "Completează un prenume valid.", now, prefill=upb.get("first_name", "")
            )
            last_name, last_name_valid = _render_name_field(
                "Nume de familie", "reg_last_name", "Completează un nume valid.", now, prefill=upb.get("last_name", "")
            )

    autorefresh_if_validating(
        ["p_valid_since", "reg_first_name_valid_since", "reg_last_name_valid_since"],
        now,
    )

    faculty_year = st.selectbox("An de studiu", options=["I", "II", "III", "IV"])
    department = st.selectbox("Departament", options=["Automatica", "Calculatoare"])
    faculty_class, specialization = decide_class(faculty_year, department)

    if specialization:
        st.info(f"Specializare: **{specialization}**")

    all_valid = password_valid and first_name_valid and last_name_valid

    if st.button("Înregistrează-te", disabled=not all_valid):
        if password != password_confirm:
            st.error("Parolele nu coincid.")
            return

        if username_exists(connection_string, username):
            st.error("Username-ul UPB este deja asociat unui alt cont. Contactează suportul.")
            return

        if email_exists(connection_string, email):
            st.error("Adresa de email este deja înregistrată.")
            return

        if not send_otp(username, email):
            return

        st.session_state.reg_pending = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
            "year": _YEAR_TO_INT[faculty_year],
            "department": department,
            "faculty_class": faculty_class,
            "email": email,
        }
        st.session_state.reg_otp_sent_at = time.time()
        st.rerun()

    st.divider()
    if st.button("← Înapoi la autentificare UPB", use_container_width=True):
        st.session_state.pop("upb_cached", None)
        navigate_to("upb_login")


def _render_form_standard(connection_string: str) -> None:
    st.title("Register")
    now = time.time()

    password = password_confirm = ""
    password_valid = False
    first_name = last_name = email = ""
    first_name_valid = last_name_valid = email_valid = False

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
        if password != password_confirm:
            st.error("Passwords do not match.")
        else:
            st.success("Passwords match.")
            first_name, first_name_valid = _render_name_field("First Name", "reg_first_name", "Complete a valid first name.", now)
            last_name, last_name_valid = _render_name_field("Last Name", "reg_last_name", "Complete a valid last name.", now)

    if first_name_valid and last_name_valid:
        email = st.text_input("Email", key="reg_email")
        e_placeholder = st.empty()
        email_valid = timing_placeholder(e_placeholder, "e_valid_since", email, _EMAIL_REQUIREMENTS)
        validate_field(email_valid, "e_valid_since", "Complete a valid email address.", now)

    autorefresh_if_validating(
        ["u_valid_since", "p_valid_since", "reg_first_name_valid_since", "reg_last_name_valid_since", "e_valid_since"],
        now,
    )

    faculty_year = st.selectbox("Faculty Year", options=["I", "II", "III", "IV"])
    department = st.selectbox("Department", options=["Automatica", "Calculatoare"])
    faculty_class, specialization = decide_class(faculty_year, department)

    if specialization:
        st.info(f"Specialization: **{specialization}**")

    all_valid = username_valid and password_valid and first_name_valid and last_name_valid and email_valid

    if st.button("Register", disabled=not all_valid):
        if password != password_confirm:
            st.error("Passwords do not match.")
            return

        if username_exists(connection_string, username):
            st.error("Username already exists.")
            return

        normalized_email = email.strip().lower()
        if email_exists(connection_string, normalized_email):
            st.error("An account with this email already exists.")
            return

        if not send_otp(username, normalized_email):
            return

        st.session_state.reg_pending = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
            "year": _YEAR_TO_INT[faculty_year],
            "department": department,
            "faculty_class": faculty_class,
            "email": normalized_email,
        }
        st.session_state.reg_otp_sent_at = time.time()
        st.rerun()

    st.divider()
    if st.button("← Back to Login", use_container_width=True):
        navigate_to("upb_login")


def _on_back_to_form() -> None:
    _clear_reg_state()
    st.rerun()


def _render_verify(connection_string: str) -> None:
    pending = st.session_state.reg_pending
    username = pending["username"]
    email = pending["email"]

    st.title("Verify your email")

    verified = render_otp_screen(
        username=username,
        email=email,
        sent_at_key="reg_otp_sent_at",
        description="verification",
        verify_label="Verify & Create Account",
        back_label="← Back to Registration",
        on_back=_on_back_to_form,
        resend_fn=lambda: send_otp(username, email),
    )

    if verified:
        success = register_user(
            connection_string,
            pending["username"],
            pending["first_name"],
            pending["last_name"],
            pending["password"],
            pending["year"],
            pending["department"],
            pending["faculty_class"],
            pending["email"],
        )
        _clear_reg_state()
        st.session_state.pop("upb_cached", None)
        if not success:
            st.error("Username was taken while verifying. Please register again.")
            st.rerun()
            return

        st.success("Cont creat cu succes! Te poți autentifica acum.")
        time.sleep(1.5)
        navigate_to("upb_login")


def render_register(connection_string: str) -> None:
    if st.session_state.get("reg_pending"):
        _render_verify(connection_string)
        return

    upb = st.session_state.get("upb_cached")
    if upb:
        _render_form_upb(connection_string, upb)
    else:
        _render_form_standard(connection_string)
