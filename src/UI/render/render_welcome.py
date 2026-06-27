import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh

_DURATION = 4.0


def _welcome_html(first: str, last: str) -> str:
    return f"""
<style>
/* hide all streamlit chrome */
section[data-testid="stSidebar"],
header[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
footer {{ display: none !important; }}

.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes bounce {{
    0%, 80%, 100% {{ transform: translateY(0);   opacity: 0.3; }}
    40%            {{ transform: translateY(-10px); opacity: 1;   }}
}}

@keyframes shimmer {{
    0%   {{ background-position: -200% center; }}
    100% {{ background-position:  200% center; }}
}}

.ws-overlay {{
    position: fixed;
    inset: 0;
    background: #0E5A9C;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    flex-direction: column;
    gap: 2rem;
}}

.ws-greeting {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 1.1rem;
    font-weight: 400;
    color: rgba(255,255,255,0.65);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    animation: fadeUp 0.6s ease both;
    animation-delay: 0.1s;
}}

.ws-name {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #fff 0%, #a8d4ff 40%, #fff 60%, #a8d4ff 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: fadeUp 0.6s ease both, shimmer 2.5s linear infinite;
    animation-delay: 0.25s, 0.25s;
}}

.ws-dots {{
    display: flex;
    gap: 0.55rem;
    animation: fadeUp 0.6s ease both;
    animation-delay: 0.45s;
}}

.ws-dots span {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(255,255,255,0.85);
    display: inline-block;
    animation: bounce 1.4s ease-in-out infinite both;
}}
.ws-dots span:nth-child(1) {{ animation-delay: 0s;    }}
.ws-dots span:nth-child(2) {{ animation-delay: 0.16s; }}
.ws-dots span:nth-child(3) {{ animation-delay: 0.32s; }}
</style>

<div class="ws-overlay">
    <p class="ws-greeting">Bun venit</p>
    <h1 class="ws-name">{first} {last}</h1>
    <div class="ws-dots">
        <span></span><span></span><span></span>
    </div>
</div>
"""


def render_welcome() -> None:
    if "welcome_start" not in st.session_state:
        st.session_state.welcome_start = time.time()

    if time.time() - st.session_state.welcome_start >= _DURATION:
        st.session_state.show_welcome = False
        st.session_state.pop("welcome_start", None)
        st.rerun()
        return

    first = st.session_state.user.get("first_name", "")
    last  = st.session_state.user.get("last_name", "")

    st.markdown(_welcome_html(first, last), unsafe_allow_html=True)
    st_autorefresh(interval=500, key="welcome_refresh")
