import re

file_path = r"C:\AIPA_SARGA\Capstone Project\masks_human_project1\masks_human_project\app.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_css = r"""<style>
/* ── Base & Background ── */
.stApp {
    background: linear-gradient(135deg,
        #0a0800 0%, #110e00 50%, #0a0800 100%);
    color: #f0e6c8;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Main Header ── */
.main-header {
    background: linear-gradient(135deg,
        #1a1400 0%, #2a1f00 40%, #1a1400 100%);
    border-radius: 16px;
    padding: 30px 36px;
    margin-bottom: 24px;
    border: 1px solid rgba(212,175,55,0.4);
    box-shadow:
        0 0 40px rgba(212,175,55,0.15),
        0 8px 32px rgba(0,0,0,0.6),
        inset 0 1px 0 rgba(212,175,55,0.2);
    text-align: center;
}
.main-header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg,
        #b8860b, #ffd700, #f5c842, #ffd700, #b8860b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 200% auto;
    animation: gold-shine 3s linear infinite;
    margin: 0;
    letter-spacing: 1px;
}
@keyframes gold-shine {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}
.main-header p {
    color: #c9a84c;
    font-size: 0.95rem;
    margin: 8px 0 0 0;
    letter-spacing: 0.5px;
}

/* ── Tab Navigation ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(212,175,55,0.05);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(212,175,55,0.2);
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #c9a84c;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,
        #b8860b, #d4af37) !important;
    color: #0a0800 !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 12px rgba(212,175,55,0.4);
}

/* ── Cards ── */
.vc-card {
    background: rgba(212,175,55,0.04);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 14px;
    padding: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.vc-card:hover {
    border-color: rgba(212,175,55,0.45);
    box-shadow: 0 6px 28px rgba(212,175,55,0.1);
}
.vc-card-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #d4af37;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 14px;
}

/* ── Metric Cards ── */
.vc-metric {
    background: rgba(212,175,55,0.04);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 12px;
    padding: 18px 14px;
    text-align: center;
    backdrop-filter: blur(8px);
}
.vc-metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 6px;
}
.vc-metric-label {
    font-size: 0.72rem;
    color: #c9a84c;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

/* ── Severity Colors ── */
.sev-no\ damage, .sev-no_damage {
    color: #4ade80 !important;
}
.sev-minor    { color: #facc15 !important; }
.sev-moderate { color: #fb923c !important; }
.sev-severe   { color: #f87171 !important; }
.sev-critical {
    color: #ff4444 !important;
    text-shadow: 0 0 20px rgba(255,68,68,0.5);
    animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.6; }
}

/* ── Damage Report Card ── */
.claim-ticket {
    background: rgba(212,175,55,0.04);
    border: 1px solid rgba(212,175,55,0.18);
    border-top: 4px solid #d4af37;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.5);
}
.claim-ticket h3 {
    color: #d4af37;
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0 0 18px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(212,175,55,0.18);
}
.claim-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid rgba(212,175,55,0.05);
    font-size: 0.88rem;
}
.claim-row:last-child { border-bottom: none; }
.claim-label {
    color: #c9a84c;
    font-weight: 500;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.claim-value {
    color: #f0e6c8;
    font-weight: 600;
    text-align: right;
}
.claim-cost {
    color: #ffd700;
    font-weight: 800;
    font-size: 1.1rem;
}

/* ── Upload Zone ── */
[data-testid="stFileUploader"] {
    background: rgba(212,175,55,0.02);
    border: 2px dashed rgba(212,175,55,0.4);
    border-radius: 12px;
    padding: 8px;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #d4af37;
    background: rgba(212,175,55,0.06);
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,
        #b8860b 0%, #d4af37 100%);
    color: #0a0800;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 12px 24px;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(212,175,55,0.3);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(212,175,55,0.5);
    color: #0a0800;
}
.stButton > button:active {
    transform: translateY(0);
}

/* ── Chatbot Messages ── */
.chat-bubble-bot {
    background: rgba(26,20,0,0.8);
    border: 1px solid rgba(212,175,55,0.2);
    border-radius: 4px 14px 14px 14px;
    padding: 12px 16px;
    color: #f0e6c8;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 85%;
    margin-bottom: 10px;
}
.chat-bubble-user {
    background: linear-gradient(135deg,
        #b8860b, #d4af37);
    border: none;
    border-radius: 14px 4px 14px 14px;
    padding: 12px 16px;
    color: #0a0800;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 85%;
    margin-left: auto;
    margin-bottom: 10px;
}

/* ── Verdict Badges ── */
.verdict-covered {
    background: rgba(22,163,74,0.1);
    border: 1px solid rgba(22,163,74,0.3);
    border-left: 4px solid #16a34a;
    border-radius: 8px;
    padding: 12px 16px;
    color: #4ade80;
}
.verdict-partial {
    background: rgba(234,88,12,0.1);
    border: 1px solid rgba(234,88,12,0.3);
    border-left: 4px solid #ea580c;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fb923c;
}
.verdict-denied {
    background: rgba(220,38,38,0.1);
    border: 1px solid rgba(220,38,38,0.3);
    border-left: 4px solid #dc2626;
    border-radius: 8px;
    padding: 12px 16px;
    color: #f87171;
}

/* ── Streamlit overrides ── */
.stApp { background-color: transparent !important; }
.stMarkdown p { color: #f0e6c8; }
[data-testid="stSidebar"] {
    background: #0a0800;
    border-right: 1px solid rgba(212,175,55,0.2);
}
section[data-testid="stMain"] {
    background: transparent;
}
.stSpinner > div {
    border-top-color: #d4af37 !important;
}
div[data-testid="stVerticalBlock"] {
    gap: 1rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0800; }
::-webkit-scrollbar-thumb {
    background: rgba(212,175,55,0.4);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #d4af37;
}
</style>"""

# Find existing <style> block and replace it
pattern = re.compile(r"<style>.*?</style>", re.DOTALL)
new_content = pattern.sub(new_css, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("CSS updated successfully to gold theme.")
