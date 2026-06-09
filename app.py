"""
app.py — DriveSure AI Corporate Claims Portal
=================================================
Enterprise claims management system with:
  Tab 1 — Vehicle Damage Analyzer (YOLOv8 Segmentation + OpenCV Fallback)
  Tab 2 — Interactive Claims Assistant (IRDAI compliant FAQ and guided claim registration)
"""

import os
import io
import re
import html
import sys
import uuid
import datetime
import numpy as np
import streamlit as st
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import predict_segmentation as engine
import chatbot

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DriveSure AI | Claims Management Portal",
    layout="wide",
    initial_sidebar_state="auto",
)

# ─── Professional CSS Theme ──────────────────────────────────────────────────
# ─── UI Theme State ───────────────────────────────────────────────────────────
if "theme_mode_select" not in st.session_state:
    st.session_state.theme_mode_select = "Light"
theme_mode = st.session_state.theme_mode_select

LIGHT_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #e2e8f0;
    font-family: 'Plus Jakarta Sans','Segoe UI',system-ui,sans-serif;
    color: #1e293b;
}

/* ── Corporate Header ── */
.main-header {
    background: #ffffff;
    border-radius: 0;
    padding: 24px 40px;
    border-bottom: 3px solid #1e3a8a;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
}
.main-header h1 {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #64748b;
    font-size: 0.875rem;
    margin-top: 4px;
    font-weight: 500;
}

/* ── Refined Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-radius: 8px 8px 0 0;
    padding: 0;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0;
    color: #64748b;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 14px 32px;
    border-right: 1px solid #cbd5e1;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #f1f5f9;
    color: #1e3a8a;
}
.stTabs [aria-selected="true"] {
    background: #1e3a8a !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ── Premium Cards ── */
.vc-card {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
}
.vc-card-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #1e3a8a;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #cbd5e1;
}

/* ── Balanced Metrics ── */
.vc-metric {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-top: 3px solid #1e3a8a;
    border-radius: 8px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
}
.vc-metric-value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 8px;
    color: #0f172a;
}
.vc-metric-label {
    font-size: 0.7rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 700;
}

/* ── Severity Colors ── */
.sev-no\ damage,.sev-no_damage { color:#16a34a !important; }
.sev-minor    { color: #ea580c !important; }
.sev-moderate { color: #dc2626 !important; }
.sev-severe   { color: #b91c1c !important; }
.sev-critical {
    color: #991b1b !important;
    font-weight: 900 !important;
    animation: crit 2s infinite;
}
@keyframes crit {
    0%,100%{opacity:1} 50%{opacity:0.6}
}

/* ── Claims Report ── */
.claim-ticket {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 32px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}
.claim-ticket h3 {
    font-size: 0.85rem;
    font-weight: 800;
    color: #1e3a8a;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid #cbd5e1;
}
.claim-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #cbd5e1;
    font-size: 0.9rem;
}
.claim-row:last-child { border-bottom: none; }
.claim-label {
    color: #64748b;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.claim-value {
    color: #0f172a;
    font-weight: 600;
}
.claim-cost {
    color: #16a34a;
    font-weight: 800;
    font-size: 1.15rem;
}

/* ── File Uploader Override ── */
[data-testid="stFileUploader"] {
    background: #e2e8f0;
    border: 2px dashed #94a3b8;
    border-radius: 8px;
    padding: 12px;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #1e3a8a;
    background: #f1f5f9;
}

/* ── Flat Action Buttons ── */
.stButton > button,
.stFormSubmitButton > button {
    background: #1e3a8a;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 12px 24px;
    letter-spacing: 0.4px;
    transition: all 0.2s;
    box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.2);
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.3);
}
.stButton > button:active,
.stFormSubmitButton > button:active {
    transform: translateY(0);
    background: #172554;
}

/* ── Professional Chat Bubble System ── */
.chat-bubble-bot {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #1e3a8a;
    border-radius: 0 10px 10px 10px;
    padding: 14px 18px;
    color: #1e293b;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 85%;
    margin-bottom: 12px;
}
.chat-bubble-user {
    background: #1e3a8a;
    border: none;
    border-radius: 10px 0 10px 10px;
    padding: 14px 18px;
    color: #ffffff;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 85%;
    margin-left: auto;
    margin-bottom: 12px;
}

/* ── IRDAI Verdict Badges ── */
.verdict-covered {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    border-radius: 6px;
    padding: 16px 20px;
    color: #166534;
    font-size: 0.9rem;
}
.verdict-partial {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-left: 4px solid #ea580c;
    border-radius: 6px;
    padding: 16px 20px;
    color: #9a3412;
    font-size: 0.9rem;
}
.verdict-denied {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid #dc2626;
    border-radius: 6px;
    padding: 16px 20px;
    color: #991b1b;
    font-size: 0.9rem;
}

/* ── Custom overrides ── */
.stMarkdown p { color: #475569; line-height: 1.7; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #cbd5e1;
}
.stSpinner > div {
    border-top-color: #1e3a8a !important;
}
.stSuccess {
    background: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: 6px !important;
    color: #166534 !important;
}
section[data-testid="stMain"] {
    background: #e2e8f0 !important;
    padding: 2rem 3rem 5rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #e2e8f0; }
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #1e3a8a;
}

/* ── Chat Container ── */
.chat-wrap {
    height: 480px;
    overflow-y: auto;
    padding: 1.5rem;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow: inset 0 1px 3px 0 rgba(0,0,0,0.01);
}
.chat-time {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.3rem;
    text-align: right;
}
.chat-avatar-bot {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1e3a8a;
    margin-right: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Download Button ── */
.stDownloadButton > button {
    background: #ffffff;
    color: #1e3a8a;
    border: 1px solid #1e3a8a;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 12px 24px;
    transition: all 0.2s;
}
.stDownloadButton > button:hover {
    background: #1e3a8a;
    color: #ffffff;
}

/* Ensure sidebar collapse/expand buttons are visible */
[data-testid="stSidebar"] button svg,
[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="collapsedControl"] button svg {
    fill: #1e3a8a !important;
    color: #1e3a8a !important;
}
</style>
"""

DARK_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #0f172a;
    font-family: 'Plus Jakarta Sans','Segoe UI',system-ui,sans-serif;
    color: #cbd5e1;
}

/* ── Corporate Header ── */
.main-header {
    background: #1e293b;
    border-radius: 0;
    padding: 24px 40px;
    border-bottom: 3px solid #2563eb;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
}
.main-header h1 {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #60a5fa;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94a3b8;
    font-size: 0.875rem;
    margin-top: 4px;
    font-weight: 500;
}

/* ── Refined Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1e293b;
    border-radius: 8px 8px 0 0;
    padding: 0;
    border: 1px solid #334155;
    border-bottom: none;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0;
    color: #94a3b8;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 14px 32px;
    border-right: 1px solid #334155;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #334155;
    color: #60a5fa;
}
.stTabs [aria-selected="true"] {
    background: #2563eb !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ── Premium Cards ── */
.vc-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px 0 rgba(0,0,0,0.2);
}
.vc-card-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #334155;
}

/* ── Balanced Metrics ── */
.vc-metric {
    background: #1e293b;
    border: 1px solid #334155;
    border-top: 3px solid #2563eb;
    border-radius: 8px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 1px 3px 0 rgba(0,0,0,0.2);
}
.vc-metric-value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 8px;
    color: #f8fafc;
}
.vc-metric-label {
    font-size: 0.7rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 700;
}

/* ── Severity Colors ── */
.sev-no\ damage,.sev-no_damage { color:#4ade80 !important; }
.sev-minor    { color: #fb923c !important; }
.sev-moderate { color: #f87171 !important; }
.sev-severe   { color: #ef4444 !important; }
.sev-critical {
    color: #f87171 !important;
    font-weight: 900 !important;
    animation: crit 2s infinite;
}
@keyframes crit {
    0%,100%{opacity:1} 50%{opacity:0.6}
}

/* ── Claims Report ── */
.claim-ticket {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 32px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
}
.claim-ticket h3 {
    font-size: 0.85rem;
    font-weight: 800;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid #334155;
}
.claim-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #334155;
    font-size: 0.9rem;
}
.claim-row:last-child { border-bottom: none; }
.claim-label {
    color: #94a3b8;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.claim-value {
    color: #f8fafc;
    font-weight: 600;
}
.claim-cost {
    color: #4ade80;
    font-weight: 800;
    font-size: 1.15rem;
}

/* ── File Uploader Override ── */
[data-testid="stFileUploader"] {
    background: #1e293b;
    border: 2px dashed #475569;
    border-radius: 8px;
    padding: 12px;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #2563eb;
    background: #1e293b;
}

/* ── Flat Action Buttons ── */
.stButton > button,
.stFormSubmitButton > button {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 12px 24px;
    letter-spacing: 0.4px;
    transition: all 0.2s;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #3b82f6;
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
}
.stButton > button:active,
.stFormSubmitButton > button:active {
    transform: translateY(0);
    background: #1d4ed8;
}

/* ── Professional Chat Bubble System ── */
.chat-bubble-bot {
    background: #334155;
    border: 1px solid #475569;
    border-left: 4px solid #3b82f6;
    border-radius: 0 10px 10px 10px;
    padding: 14px 18px;
    color: #f8fafc;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 85%;
    margin-bottom: 12px;
}
.chat-bubble-user {
    background: #2563eb;
    border: none;
    border-radius: 10px 0 10px 10px;
    padding: 14px 18px;
    color: #ffffff;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 85%;
    margin-left: auto;
    margin-bottom: 12px;
}

/* ── IRDAI Verdict Badges ── */
.verdict-covered {
    background: #064e3b;
    border: 1px solid #047857;
    border-left: 4px solid #4ade80;
    border-radius: 6px;
    padding: 16px 20px;
    color: #a7f3d0;
    font-size: 0.9rem;
}
.verdict-partial {
    background: #7c2d12;
    border: 1px solid #b45309;
    border-left: 4px solid #fb923c;
    border-radius: 6px;
    padding: 16px 20px;
    color: #ffedd5;
    font-size: 0.9rem;
}
.verdict-denied {
    background: #7f1d1d;
    border: 1px solid #b91c1c;
    border-left: 4px solid #f87171;
    border-radius: 6px;
    padding: 16px 20px;
    color: #f87171;
    font-size: 0.9rem;
}

/* ── Custom overrides ── */
.stMarkdown p, .stMarkdown li { color: #cbd5e1; line-height: 1.7; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: #f8fafc;
}
[data-testid="stSidebar"] {
    background: #1e293b;
    border-right: 1px solid #334155;
}
.stSpinner > div {
    border-top-color: #2563eb !important;
}
.stSuccess {
    background: #064e3b !important;
    border: 1px solid #047857 !important;
    border-radius: 6px !important;
    color: #a7f3d0 !important;
}
section[data-testid="stMain"] {
    background: #0f172a !important;
    padding: 2rem 3rem 5rem !important;
}

/* Override hardcoded #475569 color inside markdown divs (like the footer) in dark mode */
div[style*="color:#475569"], div[style*="color: #475569"] {
    color: #cbd5e1 !important;
}

/* Streamlit native widget styling overrides */
div[data-testid="stTextInput"] input {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #64748b !important;
}
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
}
ul[role="listbox"] {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
}
ul[role="listbox"] li {
    color: #cbd5e1 !important;
    background-color: #1e293b !important;
}
ul[role="listbox"] li:hover {
    background-color: #334155 !important;
    color: #f8fafc !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #2563eb;
}

/* ── Chat Container ── */
.chat-wrap {
    height: 480px;
    overflow-y: auto;
    padding: 1.5rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow: inset 0 1px 3px 0 rgba(0,0,0,0.2);
}
.chat-time {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.3rem;
    text-align: right;
}
.chat-avatar-bot {
    font-size: 0.85rem;
    font-weight: 700;
    color: #60a5fa;
    margin-right: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Download Button ── */
.stDownloadButton > button {
    background: #1e293b;
    color: #60a5fa;
    border: 1px solid #60a5fa;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 12px 24px;
    transition: all 0.2s;
}
.stDownloadButton > button:hover {
    background: #2563eb;
    color: #ffffff;
    border-color: #2563eb;
}

/* Ensure sidebar collapse/expand/hamburger buttons are visible */
[data-testid="stSidebar"] button svg,
[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="collapsedControl"] button svg {
    fill: #60a5fa !important;
    color: #60a5fa !important;
}
</style>
"""

if theme_mode == "Dark":
    st.markdown(DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# ─── Sidebar Color Config ─────────────────────────────────────────────────────
sb_header_color = "#60a5fa" if theme_mode == "Dark" else "#1e3a8a"
sb_desc_color = "#94a3b8" if theme_mode == "Dark" else "#64748b"
ctx_card_style = "background:#1e293b;border:1px solid #3b82f6;" if theme_mode == "Dark" else "background:#f0f4ff;border:1px solid #1e3a8a;"


# ─── Session State Init ───────────────────────────────────────────────────────
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = uuid.uuid4().hex
if "chat_history" not in st.session_state:
    sid = st.session_state.chat_session_id
    _, hist = chatbot.process_message(sid, "hi")
    st.session_state.chat_history = hist
if "last_detection" not in st.session_state:
    st.session_state.last_detection = None

# ─── Sidebar Settings ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;color:{sb_header_color};font-size:1.2rem;margin-bottom:1.5rem;">System Settings</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{sb_header_color};margin-bottom:0.4rem;">DETECTION SENSITIVITY</div>', unsafe_allow_html=True)
    sensitivity = st.slider(
        "Sensitivity",
        min_value=10,
        max_value=100,
        value=75,
        step=5,
        label_visibility="collapsed",
        key="sensitivity_slider"
    )
    st.markdown(f'<div style="font-size:0.75rem;color:{sb_desc_color};margin-top:-0.3rem;margin-bottom:1.5rem;">Higher sensitivity detects more subtle damage but may increase false positives.</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{sb_header_color};margin-bottom:0.4rem;">MASK OVERLAY ALPHA</div>', unsafe_allow_html=True)
    mask_alpha = st.slider(
        "Mask Alpha",
        min_value=0.0,
        max_value=1.0,
        value=0.42,
        step=0.05,
        label_visibility="collapsed",
        key="alpha_slider"
    )
    st.markdown(f'<div style="font-size:0.75rem;color:{sb_desc_color};margin-top:-0.3rem;margin-bottom:1.5rem;">Opacity of the colored damage masks overlaid on the vehicle.</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{sb_header_color};margin-bottom:0.4rem;margin-top:1rem;">UI THEME MODE</div>', unsafe_allow_html=True)
    st.selectbox(
        "Theme Mode",
        options=["Light", "Dark"],
        index=0 if st.session_state.theme_mode_select == "Light" else 1,
        label_visibility="collapsed",
        key="theme_mode_select"
    )

    st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{sb_header_color};margin-bottom:0.4rem;margin-top:1rem;">GEMINI API KEY</div>', unsafe_allow_html=True)
    st.text_input(
        "Gemini API Key",
        value=st.session_state.get("user_gemini_api_key", ""),
        type="password",
        placeholder="Paste your Gemini API Key here...",
        label_visibility="collapsed",
        key="user_gemini_api_key"
    )

# ─── Helper: format chat text ────────────────────────────────────────────────
def _fmt(raw_text: str) -> str:
    """Convert markdown bold and newlines to HTML for chat bubbles."""
    text = html.escape(raw_text)
    text = text.replace("\n", "<br>")
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return text

def get_chatbot_response(messages: list) -> str:
    try:
        ctx = st.session_state.get("claim_context", {})
        damage_context = ""
        if ctx:
            damage_context = f"""
Active assessment:
  Severity  : {ctx.get('severity','N/A')}
  Damage    : {ctx.get('damage_pct','N/A')}%
  Cost      : {ctx.get('cost_range','N/A')}
Use these exact values if asked about costs.
"""
        SYSTEM_PROMPT = """You are ClaimBot, an expert auto insurance claim assistant for Indian users.
Guide users step by step through their vehicle insurance claim.
"""
        full_prompt = SYSTEM_PROMPT + damage_context

        import google.generativeai as genai
        import time

        # Configure API key from user input sidebar, environment, or Streamlit Secrets
        api_key = (
            st.session_state.get("user_gemini_api_key")
            or os.environ.get("GEMINI_API_KEY")
        )
        if not api_key:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        if not api_key:
            return (
                "Please configure your Gemini API Key in the system settings sidebar, "
                "set it as a Streamlit Secret, or define it as the GEMINI_API_KEY "
                "environment variable to start chatting."
            )

        genai.configure(api_key=api_key)

        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [m["content"]]
            })

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            system_instruction=full_prompt
        )
        
        # Retry loop for rate limit (429) errors
        for attempt in range(3):
            try:
                resp = model.generate_content(contents)
                return resp.text
            except Exception as e:
                # If it's a 429 rate limit error, wait and retry
                if "429" in str(e) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise e
    except Exception as e:
        return (
            f"I apologise, I encountered "
            f"an error processing your "
            f"request. Please try again. "
            f"({e})"
        )

# ─── Corporate Hero ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>DriveSure AI Portal</h1>
    <p>Automated vehicle damage segmentation · Own damage liability assessment · Structured ₹ INR estimates</p>
</div>""", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Damage Analyzer", "Claim Chatbot"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DAMAGE ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_upload, col_results = st.columns([1, 1.5], gap="large")

    with col_upload:
        st.markdown('<div class="vc-card-title">Upload Vehicle Image</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload up to 5 vehicle images",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="damage_uploader"
        )
        if uploaded_files and len(uploaded_files) > 5:
            st.warning("Maximum 5 images. Only first 5 will be analyzed.")
            uploaded_files = uploaded_files[:5]

        if uploaded_files:
            cols = st.columns(min(len(uploaded_files), 5))
            for i, uf in enumerate(uploaded_files):
                with cols[i]:
                    st.image(uf,
                        caption=f"Image {i+1}",
                        use_container_width=True)
            analyze_btn = st.button(
                "Analyze Damage",
                use_container_width=True,
                key="analyze_btn"
            )
        else:
            st.markdown(f"""
            <div class="vc-card" style="text-align:center;padding:3rem 1rem;">
                <div style="font-size:1.1rem;font-weight:700;color:{sb_header_color};margin-bottom:0.5rem">IMAGE UPLOAD ZONE</div>
                <div style="color:{sb_desc_color};font-size:0.88rem;">
                    Upload clear photos of the damaged vehicle.<br>Supported formats: JPG, PNG, WEBP
                </div>
            </div>""", unsafe_allow_html=True)
            analyze_btn = False

    with col_results:
        if uploaded_files and analyze_btn:
            all_results = []

            for idx, uploaded in enumerate(uploaded_files):
                st.markdown(f"---")
                st.markdown(
                    f"**Analysis {idx+1} of "
                    f"{len(uploaded_files)} — "
                    f"{uploaded.name}**"
                )
                with st.spinner(
                    f"Analyzing image {idx+1} of "
                    f"{len(uploaded_files)}..."
                ):
                    tmp = os.path.join(
                        PROJECT_ROOT,
                        f"_tmp_upload_{idx}.jpg"
                    )
                    with open(tmp, "wb") as f:
                        f.write(uploaded.getvalue())
                    result = engine.predict(
                        tmp,
                        float(sensitivity),
                        float(mask_alpha)
                    )
                    if os.path.exists(tmp):
                        os.remove(tmp)

                all_results.append(result)
                st.session_state.last_detection = result

                ann_img  = result["annotated_image"]
                sev      = result["severity"]
                dmg_pct  = result["damage_pct"]
                cost_rng = result["cost_range_inr"]
                polys    = result["polygon_count"]
                source   = result["source"]
                conf     = result["confidence"]

                st.image(ann_img, caption=f"{sev} damage — {dmg_pct}% area affected", use_container_width=True)

                m1, m2, m3 = st.columns(3)
                sc = f"sev-{sev.lower()}"
                with m1:
                    st.markdown(f'<div class="vc-metric"><div class="vc-metric-value {sc}">{dmg_pct}%</div><div class="vc-metric-label">Damage Area</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="vc-metric"><div class="vc-metric-value {sc}">{sev}</div><div class="vc-metric-label">Severity</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="vc-metric"><div class="vc-metric-value" style="color:{sb_header_color};font-size:1.8rem;">{polys}</div><div class="vc-metric-label">Damage Zones</div></div>', unsafe_allow_html=True)

                what_i_see = result.get("what_i_see", "No damage visible.")
                now = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
                st.markdown(f"""
                <div class="claim-ticket">
                    <h3>Damage Report</h3>
                    <div class="claim-row"><span class="claim-label">Analyzed</span><span class="claim-value">{now}</span></div>
                    <div class="claim-row"><span class="claim-label">Image</span><span class="claim-value">{html.escape(uploaded.name)}</span></div>
                    <div class="claim-row"><span class="claim-label">Severity</span><span class="claim-value {sc}">{sev}</span></div>
                    <div class="claim-row"><span class="claim-label">Affected Area</span><span class="claim-value">{dmg_pct}% of visible surface</span></div>
                    <div class="claim-row"><span class="claim-label">Damage Zones</span><span class="claim-value">{polys} region(s)</span></div>
                    <div class="claim-row"><span class="claim-label">Engine</span><span class="claim-value">{source} ({conf:.0%})</span></div>
                    <div class="claim-row"><span class="claim-label">AI Observation</span><span class="claim-value" style="color:{sb_header_color};font-style:italic;">{html.escape(what_i_see)}</span></div>
                    <div class="claim-row"><span class="claim-label">Estimated Repair Cost</span><span class="claim-cost">{cost_rng}</span></div>
                </div>""", unsafe_allow_html=True)

                buf = io.BytesIO()
                ann_img.save(buf, "JPEG", quality=95)
                buf.seek(0)
                st.download_button("Download Report Image", buf,
                    f"damage_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg",
                    "image/jpeg", use_container_width=True, key=f"dl_btn_{idx}")

            # ── SUMMARY after all images ──
            if len(all_results) > 1:
                st.markdown("---")
                st.markdown("### Overall Damage Summary")

                sev_order = {
                    "No Damage":0,
                    "Minor":1,
                    "Moderate":2,
                    "Severe":3,
                    "Critical":4
                }
                worst = max(
                    all_results,
                    key=lambda r: sev_order.get(
                        r.get("severity","No Damage"), 0)
                )
                avg_pct = sum(
                    r.get("damage_pct", 0)
                    for r in all_results
                ) / len(all_results)

                total_lo = sum(
                    int(r.get("cost_range_inr","0")
                        .replace("₹","")
                        .replace(",","")
                        .split("–")[0].strip()
                        .replace("No clear damage detected","0")
                    ) for r in all_results
                    if "–" in r.get("cost_range_inr","")
                )
                total_hi = sum(
                    int(r.get("cost_range_inr","0")
                        .replace("₹","")
                        .replace(",","")
                        .split("–")[-1].strip()
                        .replace("No clear damage detected","0")
                    ) for r in all_results
                    if "–" in r.get("cost_range_inr","")
                )

                sc = f"sev-{worst['severity'].lower()}"
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown(
                        f'<div class="vc-metric">'
                        f'<div class="vc-metric-value {sc}">'
                        f'{worst["severity"]}</div>'
                        f'<div class="vc-metric-label">'
                        f'Worst Severity</div></div>',
                        unsafe_allow_html=True
                    )
                with s2:
                    st.markdown(
                        f'<div class="vc-metric">'
                        f'<div class="vc-metric-value">'
                        f'{avg_pct:.1f}%</div>'
                        f'<div class="vc-metric-label">'
                        f'Avg Damage</div></div>',
                        unsafe_allow_html=True
                    )
                with s3:
                    cost_str = (
                        f"₹{total_lo:,} – ₹{total_hi:,}"
                        if total_hi > 0
                        else "See individual reports"
                    )
                    st.markdown(
                        f'<div class="vc-metric">'
                        f'<div class="vc-metric-value"'
                        f' style="color:#16a34a;'
                        f'font-size:1.15rem;">'
                        f'{cost_str}</div>'
                        f'<div class="vc-metric-label">'
                        f'Total Est. Cost</div></div>',
                        unsafe_allow_html=True
                    )

            st.success(
                "Proceed to Claim Chatbot tab to file your insurance claim."
            )

        elif not uploaded_files:
            st.markdown(f"""
            <div class="vc-card" style="text-align:center;padding:3rem 1.5rem;">
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.3rem;font-weight:700;color:{sb_header_color};margin-bottom:0.5rem;">
                    AI-Powered Claims Processing
                </div>
                <div style="color:{sb_desc_color};font-size:0.88rem;line-height:1.7;">
                    Upload a vehicle image to instantly detect damage zones,<br>
                    compute severity, and generate an insurance claim ticket.
                </div>
            </div>
            <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-top:1rem;">
                <div class="vc-card" style="flex:1;min-width:130px;text-align:center;padding:1.2rem 0.5rem;">
                    <div style="font-size:0.72rem;font-weight:700;color:{sb_header_color};margin-bottom:0.35rem;">PIXEL SEGMENTATION</div>
                    <div style="font-size:0.8rem;color:{sb_desc_color};font-weight:500;">Precise mask overlay</div>
                </div>
                <div class="vc-card" style="flex:1;min-width:130px;text-align:center;padding:1.2rem 0.5rem;">
                    <div style="font-size:0.72rem;font-weight:700;color:{sb_header_color};margin-bottom:0.35rem;">SEVERITY SCORING</div>
                    <div style="font-size:0.8rem;color:{sb_desc_color};font-weight:500;">Dynamic own damage assessment</div>
                </div>
                <div class="vc-card" style="flex:1;min-width:130px;text-align:center;padding:1.2rem 0.5rem;">
                    <div style="font-size:0.72rem;font-weight:700;color:{sb_header_color};margin-bottom:0.35rem;">COST ESTIMATION</div>
                    <div style="font-size:0.8rem;color:{sb_desc_color};font-weight:500;">IRDAI integrated rates in INR</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INSURANCE CLAIM CHATBOT
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    # Initialize chatbot variables
    if "chat_step" not in st.session_state:
        st.session_state.chat_step = 0
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "claim_context" not in st.session_state:
        if st.session_state.get("last_detection"):
            det = st.session_state.get("last_detection")
            st.session_state.claim_context = {
                "severity": det.get("severity"),
                "damage_pct": det.get("damage_pct"),
                "cost_range": det.get("cost_range_inr")
            }
        else:
            st.session_state.claim_context = {}

    chat_col, info_col = st.columns([1.6, 1], gap="large")

    with chat_col:
        st.markdown("### Claims Management Assistant")

        # ── Render chat history ─────────────────────────────────────────────
        history = st.session_state.chat_history
        chat_html = '<div class="chat-wrap" id="chat-scroll">'
        for msg in history:
            role = msg["role"]
            text = _fmt(msg["text"])
            t    = msg.get("time", "")
            if role == "user":
                chat_html += (
                    f'<div style="display:flex;flex-direction:column;align-items:flex-end;">'
                    f'<div class="chat-bubble-user">{text}</div>'
                    f'<div class="chat-time">{t}</div></div>'
                )
            else:
                chat_html += (
                    f'<div style="display:flex;flex-direction:column;align-items:flex-start;">'
                    f'<div style="display:flex;align-items:flex-start;gap:0.4rem;">'
                    f'<span class="chat-avatar-bot">Assistant:</span>'
                    f'<div class="chat-bubble-bot">{text}</div></div>'
                    f'<div class="chat-time">{t}</div></div>'
                )
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # ── Input ────────────────────────────────────────────────────────────
        with st.form("chat_form", clear_on_submit=True):
            inp_col, btn_col = st.columns([5, 1])
            with inp_col:
                user_input = st.text_input(
                    "Message",
                    placeholder="Type your message here... (e.g. 'new claim', 'what documents are required?')",
                    label_visibility="collapsed",
                    key="chat_input"
                )
            with btn_col:
                send = st.form_submit_button("Send", use_container_width=True)

        if send and user_input.strip():
            sid = st.session_state.chat_session_id
            det_ctx = st.session_state.last_detection
            ctx = None
            if det_ctx:
                ctx = {
                    "severity":       det_ctx.get("severity"),
                    "damage_pct":     det_ctx.get("damage_pct"),
                    "cost_range_inr": det_ctx.get("cost_range_inr"),
                }
            _, new_history = chatbot.process_message(sid, user_input.strip(), detection_context=ctx)
            st.session_state.chat_history = new_history
            st.rerun()

        # ── Quick action buttons ─────────────────────────────────────────────
        st.markdown("**Quick Actions:**")
        qc1, qc2, qc3, qc4 = st.columns(4)
        with qc1:
            if st.button(
                "New Claim",
                key="btn_new_claim",
                use_container_width=True
            ):
                # Reset session and start fresh claim
                st.session_state.chat_step = 1
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.session_state.chat_session_id = \
                    str(__import__('uuid')
                        .uuid4())[:12]
                
                # Also reset the backend session inside chatbot.py
                chatbot.reset_session(st.session_state.chat_session_id)
                # Prime the backend claim flow
                _, h = chatbot.process_message(st.session_state.chat_session_id, "new claim")
                # Keep chat_history in sync with initial bot prompt
                for msg in h:
                    st.session_state.chat_history.append({
                        "role": msg["role"],
                        "text": msg["text"],
                        "time": msg.get("time", "")
                    })

                # Create new DB session
                import db
                ctx = st.session_state.get(
                    "claim_context", {})
                db.create_session(
                    session_id=st.session_state
                        .chat_session_id,
                    severity=ctx.get("severity"),
                    damage_pct=ctx.get("damage_pct"),
                    cost_range=ctx.get("cost_range")
                )
                st.rerun()

        with qc2:
            if st.button(
                "Documents Required",
                key="btn_docs",
                use_container_width=True
            ):
                # Send fixed message to LLM
                # DO NOT change chat_step
                doc_query = (
                    "What documents are required "
                    "to submit an insurance claim?"
                )
                st.session_state.messages.append({
                    "role": "user",
                    "content": doc_query
                })
                # Sync chat_history
                st.session_state.chat_history.append({
                    "role": "user",
                    "text": doc_query,
                    "time": __import__('datetime').datetime.now().strftime("%I:%M %p")
                })
                import db
                db.save_message(
                    session_id=st.session_state
                        .chat_session_id,
                    role="user",
                    content=doc_query
                )
                # Get LLM response
                response = get_chatbot_response(
                    st.session_state.messages
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                # Sync chat_history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "text": response,
                    "time": __import__('datetime').datetime.now().strftime("%I:%M %p")
                })
                db.save_message(
                    session_id=st.session_state
                        .chat_session_id,
                    role="assistant",
                    content=response
                )
                st.rerun()

        with qc3:
            if st.button(
                "Timeline Info",
                key="btn_timeline",
                use_container_width=True
            ):
                # Send fixed message to LLM
                # DO NOT change chat_step
                timeline_query = (
                    "How long does each stage of "
                    "the insurance claim process "
                    "take? Please explain the "
                    "complete timeline."
                )
                st.session_state.messages.append({
                    "role": "user",
                    "content": timeline_query
                })
                # Sync chat_history
                st.session_state.chat_history.append({
                    "role": "user",
                    "text": timeline_query,
                    "time": __import__('datetime').datetime.now().strftime("%I:%M %p")
                })
                import db
                db.save_message(
                    session_id=st.session_state
                        .chat_session_id,
                    role="user",
                    content=timeline_query
                )
                # Get LLM response
                response = get_chatbot_response(
                    st.session_state.messages
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                # Sync chat_history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "text": response,
                    "time": __import__('datetime').datetime.now().strftime("%I:%M %p")
                })
                db.save_message(
                    session_id=st.session_state
                        .chat_session_id,
                    role="assistant",
                    content=response
                )
                st.rerun()

        with qc4:
            if st.button(
                "Reset Chat",
                key="btn_reset",
                use_container_width=True,
                type="secondary"
            ):
                # Clear chat history only
                # Keep damage assessment context
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.session_state.chat_step = 0
                st.session_state.chat_session_id = \
                    str(__import__('uuid')
                        .uuid4())[:12]
                
                # Reset chatbot backend session
                chatbot.reset_session(st.session_state.chat_session_id)
                # Initialize chatbot session
                _, h = chatbot.process_message(st.session_state.chat_session_id, "hi")
                for msg in h:
                    st.session_state.chat_history.append({
                        "role": msg["role"],
                        "text": msg["text"],
                        "time": msg.get("time", "")
                    })

                import db
                db.create_session(
                    session_id=st.session_state
                        .chat_session_id
                )
                st.rerun()

    with info_col:
        st.markdown("### Claims Help Reference")

        topics = [
            ("File a Claim",      "Guide you step-by-step through registering a new claim"),
            ("Documents Required", "List all documents required for claim submission"),
            ("Processing Time",   "Explain how long each stage takes"),
            ("Deductibles",       "IRDAI compulsory excess and voluntary deductibles"),
            ("Coverage Policy",   "Own Damage, Third Party, NCB, depreciation limits"),
            ("Claim Tracking",    "Track your existing claim by Claim ID"),
            ("Appeals Process",   "How to dispute or appeal a rejected claim"),
            ("Payout Methods",    "Cashless settlement, NEFT, and cheque options"),
        ]
        for title, desc in topics:
            st.markdown(f"""
            <div class="vc-card" style="padding:0.9rem 1rem;margin-bottom:0.5rem;">
                <div>
                    <div style="font-weight:600;color:{sb_header_color};font-size:0.88rem;">{title}</div>
                    <div style="color:{sb_desc_color};font-size:0.78rem;margin-top:0.2rem;">{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Show AI result context if available
        if st.session_state.last_detection:
            det = st.session_state.last_detection
            sev = det.get("severity", "—")
            sev_class = f"sev-{sev.lower()}"
            st.markdown(f"""
            <div class="vc-card" style="{ctx_card_style}padding:1rem;margin-top:0.5rem;">
                <div class="vc-card-title" style="border-bottom: 2px solid #cbd5e1;">Active Assessment Context</div>
                <div style="font-size:0.85rem;line-height:1.8;">
                    <span class="{sev_class}">⬤</span> <b>Severity:</b> {sev}<br>
                    <b>Damage Area:</b> {det.get('damage_pct', '—')}% of surface<br>
                    <b>Estimated Cost:</b> {det.get('cost_range_inr', '—')}
                </div>
                <div style="font-size:0.75rem;color:{sb_header_color};margin-top:0.6rem;font-weight:600;">
                    Status: Shared with claim assistant.
                </div>
            </div>""", unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:{sb_desc_color};font-size:0.75rem;padding:0.3rem 0;">
    DriveSure AI Claims Management Portal · Multi-Modal Damage Segmentation Engine · All repair costs strictly structured in INR (₹)
</div>""", unsafe_allow_html=True)
