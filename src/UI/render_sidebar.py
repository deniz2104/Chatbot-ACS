import streamlit as st
from src.UI.render_conversations import render_past_conversations
from src.UI.delete_chatbot_session import delete_session
from src.UI.conversation import create_user_conversation, conversation_history
from src.UI.conversation_context import save_conversation_context

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

        if st.button("Log out", use_container_width=True,
             on_click=delete_session, args=(connection_string,)):
            st.success("Logged out successfully.")
            st.rerun()
