#!/usr/bin/env python3
"""Zalopay BD Agent — Streamlit Chat UI"""
import os
import streamlit as st
from openai import OpenAI
from config import MODEL, MAX_TOKENS, SYSTEM_PROMPT

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zalopay BD Agent",
    page_icon="💙",
    layout="centered",
)

# ─── CSS injection ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] > .main { background: #f0f2f5; }
  [data-testid="stHeader"] { display: none; }
  footer { visibility: hidden; }
  /* Suggestion chip buttons */
  div[data-testid="stHorizontalBlock"] button {
    border: 1px solid #0068FF !important;
    color: #0068FF !important;
    background: white !important;
    border-radius: 20px !important;
    font-size: 13px !important;
  }
  div[data-testid="stHorizontalBlock"] button:hover {
    background: #e8f0ff !important;
  }
  /* New-chat button style */
  [data-testid="stMainBlockContainer"] > div:first-child button[kind="secondary"] {
    border-radius: 20px !important;
  }
</style>
""", unsafe_allow_html=True)


# ─── Env + OpenAI client ─────────────────────────────────────────────────────
def _load_env():
    path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@st.cache_resource
def _build_client() -> OpenAI:
    _load_env()
    return OpenAI(
        api_key=os.environ.get("LLM_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL"),
    )


def _stream_reply(client: OpenAI, messages: list):
    """Yield token strings from the LLM stream."""
    for chunk in client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        stream=True,
    ):
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ─── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

client = _build_client()


# ─── Core send handler ────────────────────────────────────────────────────────
def handle_send(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(_stream_reply(client, st.session_state.messages))
        except Exception as exc:
            reply = f"⚠️ Lỗi kết nối API: {exc}"
            st.error(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ─── Header ───────────────────────────────────────────────────────────────────
h_col, btn_col = st.columns([7, 1])
with h_col:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0068FF, #0054CC);
        color: white; padding: 14px 18px; border-radius: 12px;
        margin-bottom: 6px; line-height: 1.55;
    ">
        <b style="font-size:15px;">💙 Hiếu Nghĩa — Zalopay BD</b><br>
        <span style="font-size:12px;opacity:.88;">
            Chuyên viên Phát triển Kinh doanh &nbsp;·&nbsp;
            <span style="color:#4cfa8c">●</span> Online
        </span>
    </div>""", unsafe_allow_html=True)
with btn_col:
    st.markdown("<div style='padding-top:10px'></div>", unsafe_allow_html=True)
    if st.button("↺ Mới", use_container_width=True, key="new_chat"):
        st.session_state.messages = []
        st.rerun()


# ─── Conversation display ─────────────────────────────────────────────────────
WELCOME = (
    "Xin chào! Tôi là **Hiếu Nghĩa** từ đội BD Zalopay 👋\n\n"
    "Anh/chị đang kinh doanh trong lĩnh vực nào và cần tư vấn "
    "giải pháp thanh toán gì ạ?"
)
SUGGESTIONS = [
    "Tích hợp QR thanh toán",
    "Phí cổng thanh toán",
    "BNPL mua trước trả sau",
    "Quy trình onboarding merchant",
]

# Replay conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Empty-state: welcome + suggestion chips
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(WELCOME)
    chips = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        if chips[i % 2].button(text, key=f"chip_{i}", use_container_width=True):
            handle_send(text)


# ─── Chat input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Nhập tin nhắn..."):
    handle_send(prompt)
