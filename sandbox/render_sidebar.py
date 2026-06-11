import streamlit as st
from sandbox.render_conversations import render_past_conversations
from sandbox.delete_chatbot_session import delete_session
from sandbox.conversation import create_user_conversation, conversation_history
from sandbox.conversation_context import save_conversation_context


def render_sidebar() -> None:
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
            save_conversation_context()
            create_user_conversation()
            conversation_history()
            st.rerun()

        st.divider()
        render_past_conversations()
        st.divider()

        if st.button("Log out", use_container_width=True, on_click=delete_session):
            st.success("Logged out successfully.")
            st.rerun()
