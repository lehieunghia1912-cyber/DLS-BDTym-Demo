#!/usr/bin/env python3
"""Zalopay BD Agent — Streamlit Chat UI with chart rendering"""
import json
import os
import re

import plotly.graph_objects as go
import streamlit as st
from openai import OpenAI

from config import MAX_TOKENS, MODEL, SYSTEM_PROMPT

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zalopay BD Agent",
    page_icon="💙",
    layout="centered",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] > .main { background: #f0f2f5; }
  [data-testid="stHeader"] { display: none; }
  footer { visibility: hidden; }
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
</style>
""", unsafe_allow_html=True)

# Zalopay palette
_BLUE    = "#0068FF"
_GREY    = "#94a3b8"
_PALETTE = ["#0068FF", "#3385FF", "#FF6B35", "#F59E0B",
            "#10B981", "#8B5CF6", "#94a3b8", "#cbd5e1"]


# ─── Env + client ─────────────────────────────────────────────────────────────
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


# ─── Chart rendering ──────────────────────────────────────────────────────────
def _colors(labels: list, highlight: str = "") -> list:
    if highlight:
        return [_BLUE if highlight.lower() in lbl.lower() else _GREY for lbl in labels]
    return _PALETTE[: len(labels)]


def render_chart(data: dict):
    ctype     = data.get("type", "bar")
    title     = data.get("title", "")
    highlight = data.get("highlight", "Zalopay")

    if ctype == "bar":
        labels = data.get("labels", [])
        values = data.get("values", [])
        unit   = data.get("unit", "")
        colors = _colors(labels, highlight)
        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=colors,
            text=[f"{v}{unit}" for v in values],
            textposition="outside",
        ))
        fig.update_layout(
            title=title, plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, margin=dict(t=50, b=20, l=20, r=20),
            yaxis=dict(showgrid=True, gridcolor="#eee"),
        )
        st.plotly_chart(fig, use_container_width=True)

    elif ctype == "pie":
        labels = data.get("labels", [])
        values = data.get("values", [])
        pull   = [0.08 if "zalopay" in lbl.lower() else 0 for lbl in labels]
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=_PALETTE[: len(labels)],
            pull=pull, textinfo="label+percent",
            hole=0.3,
        ))
        fig.update_layout(
            title=title, paper_bgcolor="white",
            margin=dict(t=50, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    elif ctype == "line":
        x_labels = data.get("labels", [])
        series   = data.get("series", [])
        fig = go.Figure()
        for i, s in enumerate(series):
            is_zp = "zalopay" in s.get("name", "").lower()
            fig.add_trace(go.Scatter(
                x=x_labels, y=s.get("values", []),
                name=s.get("name", ""),
                mode="lines+markers",
                line=dict(
                    color=_BLUE if is_zp else _PALETTE[i % len(_PALETTE)],
                    width=3 if is_zp else 2,
                ),
                marker=dict(size=7 if is_zp else 5),
            ))
        fig.update_layout(
            title=title, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=50, b=20, l=20, r=20),
            yaxis=dict(showgrid=True, gridcolor="#eee"),
        )
        st.plotly_chart(fig, use_container_width=True)

    elif ctype == "table":
        headers = data.get("headers", [])
        rows    = data.get("rows", [])
        if title:
            st.markdown(f"**{title}**")
        md  = "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        md += "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
        st.markdown(md)

    else:
        st.warning(f"Loại biểu đồ không hỗ trợ: `{ctype}`")


_CHART_RE = re.compile(r"```chart\s*\n(.*?)\n```", re.DOTALL)


def render_message(content: str):
    """Render message: replace ```chart blocks with actual Plotly charts."""
    parts = _CHART_RE.split(content)
    for i, part in enumerate(parts):
        if i % 2 == 0:         # text segment
            if part.strip():
                st.markdown(part)
        else:                  # JSON chart segment
            try:
                render_chart(json.loads(part.strip()))
            except Exception as exc:
                st.warning(f"Không thể hiển thị biểu đồ: {exc}")
                st.code(part, language="json")


# ─── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

client = _build_client()


# ─── Send handler ─────────────────────────────────────────────────────────────
def handle_send(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        try:
            for token in _stream_reply(client, st.session_state.messages):
                full_text += token
                placeholder.markdown(full_text + "▌")
            placeholder.empty()
            render_message(full_text)
            reply = full_text
        except Exception as exc:
            reply = f"⚠️ Lỗi kết nối API: {exc}"
            placeholder.error(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ─── Header ───────────────────────────────────────────────────────────────────
h_col, btn_col = st.columns([7, 1])
with h_col:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0068FF,#0054CC);
        color:white;padding:14px 18px;border-radius:12px;
        margin-bottom:6px;line-height:1.55;">
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
    "So sánh MDR các giải pháp thanh toán",
    "Thị phần ví điện tử Việt Nam",
    "BNPL mua trước trả sau",
    "Quy trình onboarding merchant",
]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_message(msg["content"])
        else:
            st.markdown(msg["content"])

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
