import streamlit as st
from src.UI.utils import format_date
from src.UI.conversation_context import save_conversation_context
from src.UI.conversation import conversation_history

def render_past_conversations(connection_string: str) -> None:
    conversations: list[dict] = st.session_state.get("conversations", [])

    if not conversations:
        st.caption("Nu există conversații anterioare.")
        return

    active_id = st.session_state.get("conversation_id")

    for conv in conversations:
        conv_id = conv.get("RowKey", "")
        title = conv.get("title", "")
        is_active = conv_id == active_id

        if is_active:
            display_title = f"✏️ {title}" if title else "✏️ Conversație nouă"
        else:
            display_title = title if title else "💬 Conversație"

        if st.button(
            display_title,
            key=f"conv_{conv_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            save_conversation_context(connection_string)
            conversation_history(connection_string)
            st.session_state.conversation_id = conv_id
            st.rerun()

        date_label = format_date(conv.get("last_active", ""))
        if date_label:
            st.caption(date_label)
