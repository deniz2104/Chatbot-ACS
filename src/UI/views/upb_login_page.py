import streamlit as st

from src.UI.utils import navigate_to
from src.UI.views.upb_login import upb_login, upb_login_otp
from src.azure.db.auth.verify_user import get_username_by_email


def _clear_upb_stage() -> None:
    for key in ("upb_stage", "upb_otp_data"):
        st.session_state.pop(key, None)


def _on_upb_success(connection_string: str, userinfo: dict) -> None:
    _clear_upb_stage()
    email = userinfo.get("email", "").strip().lower()
    chatbot_username = get_username_by_email(connection_string, email)

    if chatbot_username is not None:
        st.session_state.upb_verified = {
            "email": email,
            "upb_username": userinfo.get("preferred_username", ""),
            "chatbot_username": chatbot_username,
        }
        st.session_state["login_username"] = chatbot_username
        navigate_to("login")
    else:
        st.session_state.upb_cached = {
            "username": userinfo.get("preferred_username", ""),
            "email": email,
            "first_name": userinfo.get("given_name", ""),
            "last_name": userinfo.get("family_name", ""),
        }
        navigate_to("register")


def _render_otp_step(connection_string: str) -> None:
    st.info("Contul tău necesită verificare în doi pași. Introdu codul OTP.")

    otp = st.text_input("Cod OTP", key="upb_otp_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Verifică", disabled=not otp, use_container_width=True):
            otp_data = st.session_state.upb_otp_data
            try:
                userinfo = upb_login_otp(
                    otp=otp,
                    action=otp_data["action"],
                    hidden=otp_data["hidden"],
                    cookies=otp_data["cookies"],
                    verifier=otp_data["verifier"],
                )
                _on_upb_success(connection_string, userinfo)
            except ValueError as e:
                st.error(str(e))
            except Exception:
                st.error("Eroare de conexiune. Încearcă din nou.")
    with col2:
        if st.button("← Înapoi", use_container_width=True):
            _clear_upb_stage()
            st.rerun()


def _render_credentials_step(connection_string: str) -> None:
    st.caption("Folosește credențialele contului tău UPB (login.upb.ro).")

    username = st.text_input("Username UPB", key="upb_username")
    password = st.text_input("Parolă UPB", type="password", key="upb_password")

    if st.button("Continuă", disabled=not (username and password), use_container_width=True):
        with st.spinner("Se verifică credențialele..."):
            try:
                result = upb_login(username, password)
            except ValueError as e:
                st.error(str(e))
                return
            except Exception:
                st.error("Eroare de conexiune la serverul UPB. Încearcă mai târziu.")
                return

        if isinstance(result, dict) and result.get("otp_required"):
            st.session_state.upb_stage = "otp"
            st.session_state.upb_otp_data = result
            st.rerun()
        else:
            _on_upb_success(connection_string, result)


def render_upb_login(connection_string: str) -> None:
    st.title("Autentificare UPB")
    if st.session_state.get("upb_stage") == "otp":
        _render_otp_step(connection_string)
    else:
        _render_credentials_step(connection_string)
