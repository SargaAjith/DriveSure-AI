import re

file_path = r"C:\AIPA_SARGA\Capstone Project\masks_human_project1\masks_human_project\app.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_css = r"""<style>
/* ── Base & Background ── */
.stApp {
    background: #f0f4f8;
    color: #1a202c;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Main Header ── */
.main-header {
    background: linear-gradient(135deg,
        #1a56db 0%, #1e429f 100%);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: none;
    box-shadow: 0 4px 20px rgba(26,86,219,0.25);
    text-align: center;
}
.main-header h1 {
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #bfdbfe;
    font-size: 0.95rem;
    margin: 8px 0 0 0;
}

/* ── Tab Navigation ── */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #e2e8f0;
    gap: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #4a5568;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,
        #1a56db, #1e429f) !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(26,86,219,0.3);
}

/* ── Cards ── */
.vc-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.vc-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
}
.vc-card-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #1a56db;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 14px;
}

/* ── Metric Cards ── */
.vc-metric {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 14px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.vc-metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 6px;
}
.vc-metric-label {
    font-size: 0.72rem;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

/* ── Severity Colors ── */
.sev-no\ damage, .sev-no_damage {
    color: #16a34a !important;
}
.sev-minor    { color: #ca8a04 !important; }
.sev-moderate { color: #ea580c !important; }
.sev-severe   { color: #dc2626 !important; }
.sev-critical {
    color: #991b1b !important;
    font-weight: 900 !important;
    animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.6; }
}

/* ── Damage Report Card ── */
.claim-ticket {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 4px solid #1a56db;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.claim-ticket h3 {
    color: #1a56db;
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0 0 18px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}
.claim-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid #f7fafc;
    font-size: 0.88rem;
}
.claim-row:last-child { border-bottom: none; }
.claim-label {
    color: #718096;
    font-weight: 500;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.claim-value {
    color: #1a202c;
    font-weight: 600;
    text-align: right;
}
.claim-cost {
    color: #16a34a;
    font-weight: 800;
    font-size: 1.1rem;
}

/* ── Upload Zone ── */
[data-testid="stFileUploader"] {
    background: #f8faff;
    border: 2px dashed #93c5fd;
    border-radius: 12px;
    padding: 8px;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #1a56db;
    background: #eff6ff;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,
        #1a56db 0%, #1e429f 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 12px 24px;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(26,86,219,0.3);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(26,86,219,0.4);
}
.stButton > button:active {
    transform: translateY(0);
}

/* ── Chatbot Messages ── */
.chat-bubble-bot {
    background: #f0f7ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px 14px 14px 14px;
    padding: 12px 16px;
    color: #1a202c;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 85%;
    margin-bottom: 10px;
}
.chat-bubble-user {
    background: linear-gradient(135deg,
        #1a56db, #1e429f);
    border: none;
    border-radius: 14px 4px 14px 14px;
    padding: 12px 16px;
    color: #ffffff;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 85%;
    margin-left: auto;
    margin-bottom: 10px;
}

/* ── Verdict Badges ── */
.verdict-covered {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-left: 4px solid #16a34a;
    border-radius: 8px;
    padding: 12px 16px;
    color: #15803d;
}
.verdict-partial {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-left: 4px solid #ea580c;
    border-radius: 8px;
    padding: 12px 16px;
    color: #c2410c;
}
.verdict-denied {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-left: 4px solid #dc2626;
    border-radius: 8px;
    padding: 12px 16px;
    color: #b91c1c;
}

/* ── Streamlit overrides ── */
.stApp { background-color: #f0f4f8 !important; }
.stMarkdown p { color: #4a5568; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stMain"] {
    background: #f0f4f8;
}
.stSpinner > div {
    border-top-color: #1a56db !important;
}
div[data-testid="stVerticalBlock"] {
    gap: 1rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f0f4f8; }
::-webkit-scrollbar-thumb {
    background: #93c5fd;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #1a56db;
}
</style>"""

# Find existing <style> block and replace it
pattern = re.compile(r"<style>.*?</style>", re.DOTALL)
new_content = pattern.sub(new_css, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("CSS updated successfully to light theme.")
