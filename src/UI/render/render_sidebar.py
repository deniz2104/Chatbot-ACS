import streamlit as st

from src.UI.render.render_conversations import render_past_conversations
from src.UI.session.user_session import delete_session
from src.UI.conversation.conversation import create_user_conversation, conversation_history
from src.UI.conversation.conversation_context import save_conversation_context
from src.UI.utils import format_date
from src.azure.db.crawl_diff.load_crawl_diff import load_latest_crawl_diff

def _render_url_section(label: str, urls: list[str], count: int) -> None:
    if not urls:
        return
    with st.expander(f"{label} ({count})", expanded=False):
        for url in urls:
            st.markdown(f"- [{url}]({url})")


@st.dialog("🆕 Ultimele modificări", width="large")
def _show_crawl_diff(connection_string: str) -> None:
    diff = load_latest_crawl_diff(connection_string)
    if diff is None:
        st.info("Nu există date despre ultima actualizare a bazei de cunoștințe.")
        return

    st.caption(f"Ultima actualizare: {format_date(diff['crawled_at'])}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Noi", diff["new_count"])
    col2.metric("Modificate", diff["changed_count"])
    col3.metric("Eliminate", diff["removed_count"])
    col4.metric("Nemodificate", diff["unchanged_count"])

    st.divider()
    _render_url_section("✅ Adăugate", diff["new_urls"], diff["new_count"])
    _render_url_section("✏️ Modificate", diff["changed_urls"], diff["changed_count"])
    _render_url_section("🗑️ Eliminate", diff["removed_urls"], diff["removed_count"])


def render_sidebar(connection_string: str) -> None:
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            transform: translateZ(0) !important;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 15rem !important;
            max-width: 15rem !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            min-width: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
        }
        div.element-container:has(#sidebar-spacer) + div.element-container {
            position: fixed !important;
            bottom: 0rem !important;
            left: 0rem !important;
            right: 0rem !important;
            z-index: 999 !important;
            background-color: var(--secondary-background-color) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Conversații")

        if st.button("💬 Nouă conversație", use_container_width=True):
            if st.session_state.get("messages"):
                save_conversation_context(connection_string)
                create_user_conversation(connection_string)
            conversation_history(connection_string)
            st.rerun()

        st.divider()
        render_past_conversations(connection_string)
        st.divider()

        if st.button("🆕 Ultimele modificări", use_container_width=True):
            _show_crawl_diff(connection_string)

        if st.button("Log out", use_container_width=True,
             on_click=delete_session, args=(connection_string,)):
            st.success("Logged out successfully.")
            st.rerun()
