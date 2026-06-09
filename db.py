import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_storage.db")

def create_session(session_id, severity=None, damage_pct=None, cost_range=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                state TEXT,
                claim_id TEXT,
                claim TEXT,
                history TEXT
            )
        """)
        claim_data = {
            "severity": severity,
            "damage_pct": damage_pct,
            "cost_range": cost_range
        }
        cursor.execute(
            "INSERT OR IGNORE INTO sessions (session_id, state, claim, history) VALUES (?, ?, ?, ?)",
            (session_id, "GREETING", json.dumps(claim_data), "[]")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] create_session failed: {e}")

def save_message(session_id, role, content, step_number=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT history FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            history = json.loads(row[0])
        else:
            history = []
        
        history.append({
            "role": role,
            "text": content,
            "step": step_number
        })
        
        cursor.execute(
            "UPDATE sessions SET history = ? WHERE session_id = ?",
            (json.dumps(history), session_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] save_message failed: {e}")
