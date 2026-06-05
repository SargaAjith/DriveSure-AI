import re

file_path = r"C:\AIPA_SARGA\Capstone Project\masks_human_project1\masks_human_project\app.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_css = """<style>
/* ── Base & Background ── */
.stApp {
    background: linear-gradient(135deg,
        #0a0f1e 0%, #0d1528 50%, #0a0f1e 100%);
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Main Header / Title ── */
.main-header {
    background: linear-gradient(135deg,
        #1a237e 0%, #283593 50%, #1565c0 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid rgba(100,149,237,0.3);
    box-shadow: 0 8px 32px rgba(21,101,192,0.4),
                0 0 60px rgba(21,101,192,0.1);
    text-align: center;
}
.main-header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg,
        #64b5f6, #ffffff, #64b5f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #90caf9;
    font-size: 0.95rem;
    margin: 8px 0 0 0;
    opacity: 0.9;
}

/* ── Tab Navigation ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.08);
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #90caf9;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,
        #1565c0, #1976d2) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(21,101,192,0.5);
}

/* ── Cards ── */
.vc-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 20px;
    backdrop-filter: blur(12px);
    transition: border-color 0.2s;
}
.vc-card:hover {
    border-color: rgba(100,149,237,0.4);
}
.vc-card-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #90caf9;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 14px;
}

/* ── Metric Cards ── */
.vc-metric {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
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
    color: #94a3b8;
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
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

/* ── Chat UI (Preserved) ─────────────────────────────────── */
.chat-wrap {
    height: 440px;
    overflow-y: auto;
    padding: 1.2rem;
    background: rgba(10, 11, 15, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20px; margin-bottom: 1.2rem;
    display: flex; flex-direction: column; gap: 0.9rem;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
}
.chat-bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff; padding: 0.75rem 1.2rem;
    border-radius: 20px 20px 4px 20px; max-width: 80%;
    font-size: 0.9rem; line-height: 1.5; word-wrap: break-word;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25);
}
.chat-bubble-bot {
    align-self: flex-start;
    background: rgba(30, 41, 59, 0.5) !important;
    backdrop-filter: blur(8px);
    color: #f1f5f9; padding: 0.75rem 1.2rem;
    border-radius: 20px 20px 20px 4px; max-width: 85%;
    font-size: 0.9rem; line-height: 1.6; word-wrap: break-word;
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.chat-time {
    font-size: 0.68rem; color: #64748b;
    margin-top: 0.25rem; text-align: right;
}
.chat-avatar-bot { font-size: 1.25rem; margin-right: 0.4rem; }

/* ── Other Preserved Essentials ─────────────────────────────────── */
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
button[kind="header"] { display: none !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background:#1e293b; border-radius:4px; }
</style>"""

# Find existing <style> block and replace it
pattern = re.compile(r"<style>.*?</style>", re.DOTALL)
new_content = pattern.sub(new_css, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("CSS updated successfully.")
