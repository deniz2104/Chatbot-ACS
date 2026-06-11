import streamlit as st


@st.dialog("Surse folosite în ultimul răspuns", width="large")
def _sources_modal() -> None:
    sources = st.session_state.get("last_sources", [])

    if not sources:
        st.info("Nicio interogare nu a fost făcută încă.")
        return

    st.markdown(f"**{len(sources)} surs{'ă' if len(sources) == 1 else 'e'} găsite**")
    st.divider()

    for s in sources:
        title = s.get("title", "Fără titlu")
        url = s.get("url", "")
        st.markdown(f"""
            <div style="
                padding: 0.85rem 1rem;
                border-radius: 0.6rem;
                border: 1px solid rgba(128,128,128,0.25);
                margin-bottom: 0.6rem;
                display: flex;
                align-items: center;
                gap: 0.6rem;
            ">
                <span style="font-size: 1.1rem;">🔗</span>
                <a href="{url}" target="_blank" style="
                    text-decoration: none;
                    font-weight: 500;
                    font-size: 0.95rem;
                ">{title}</a>
            </div>
        """, unsafe_allow_html=True)


def render_sources() -> None:
    sources = st.session_state.get("last_sources", [])
    count = len(sources) if sources else 0
    label = f"📎 Surse ({count})" if count else "📎 Surse"

    st.markdown("""
        <style>
        div.element-container:has(#sources-btn-marker) {
            display: none !important;
        }
        div.element-container:has(#sources-btn-marker) + div.element-container {
            position: fixed !important;
            bottom: 1.75rem !important;
            right: 4rem !important;
            z-index: 1000 !important;
            width: auto !important;
        }
        div.element-container:has(#sources-btn-marker) + div.element-container button {
            padding: 0.35rem 0.75rem !important;
            font-size: 0.85rem !important;
            border-radius: 0.5rem !important;
        }
        </style>
        <div id="sources-btn-marker"></div>
    """, unsafe_allow_html=True)

    if st.button(label, disabled=count == 0, key="sources_btn"):
        _sources_modal()
