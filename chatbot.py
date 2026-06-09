"""
chatbot.py — Insurance Claim Chatbot Engine
=============================================
Handles multi-turn conversations about vehicle damage insurance claims.
Manages session state, claim data collection, FAQs, and claim summaries.
All financial amounts displayed in Indian Rupees (₹).
"""

import re
import uuid
import os
from datetime import datetime
from typing import Optional
import json
import sqlite3

# ─── Session store (in-memory) ────────────────────────────────────────────────
_SESSIONS = {}

# ─── Database Chat Storage (SQLite) ──────────────────────────────────────────
def _init_db():
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_storage.db")
        conn = sqlite3.connect(db_path)
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
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Initialisation failed: {e}")

# Initialise database at startup
_init_db()

def _save_session_to_db(session_id: str, session_data: dict):
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_storage.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (session_id, state, claim_id, claim, history) VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                session_data.get("state"),
                session_data.get("claim_id"),
                json.dumps(session_data.get("claim", {})),
                json.dumps(session_data.get("history", []))
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Failed to save session: {e}")

def _load_session_from_db(session_id: str) -> Optional[dict]:
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_storage.db")
        if not os.path.exists(db_path):
            return None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT state, claim_id, claim, history FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "state": row[0],
                "claim_id": row[1],
                "claim": json.loads(row[2]),
                "history": json.loads(row[3])
            }
    except Exception as e:
        print(f"[Database Error] Failed to load session: {e}")
    return None

# ─── Conversation States ──────────────────────────────────────────────────────
STATE_GREETING       = "GREETING"
STATE_COLLECT_NAME   = "COLLECT_NAME"
STATE_COLLECT_POLICY = "COLLECT_POLICY"
STATE_COLLECT_EMAIL  = "COLLECT_EMAIL"
STATE_COLLECT_PHONE  = "COLLECT_PHONE"
STATE_COLLECT_DATE   = "COLLECT_DATE"
STATE_COLLECT_INCIDENT_DESC = "COLLECT_INCIDENT_DESC"  # Ask what happened to the vehicle
STATE_COLLECT_MOVING_PARKED = "COLLECT_MOVING_PARKED"  # Ask was vehicle moving or parked
STATE_COLLECT_COLLISION_TYPE = "COLLECT_COLLISION_TYPE"  # Ask collision vs non-collision
STATE_COLLECT_POLICY_TYPE    = "COLLECT_POLICY_TYPE"     # Ask policy type
STATE_COLLECT_DEDUCTIBLE     = "COLLECT_DEDUCTIBLE"      # Ask deductible amount
STATE_CONFIRM        = "CONFIRM"
STATE_SUBMITTED      = "SUBMITTED"
STATE_FAQ            = "FAQ"
STATE_IDLE           = "IDLE"

# ─── Claim causes ─────────────────────────────────────────────────────────────
CAUSES = [
    "Accident / Collision",
    "Natural Disaster (Flood, Storm, Hail)",
    "Theft / Vandalism",
    "Fire Damage",
    "Parking Incident",
    "Hit and Run",
    "Other"
]

# ─── FAQ Knowledge Base ───────────────────────────────────────────────────────
FAQ_KB = {
    "process": """**Claim Process** (Step-by-Step):
1. Upload your vehicle photo for AI damage analysis.
2. Review the damage assessment (severity and cost estimate).
3. Start a new claim via the chat and provide your details.
4. Submit the claim and receive your Claim ID.
5. Our adjuster will contact you within **2–3 business days**.
6. Approved payouts are processed in **5–7 working days**.""",

    "documents": """**Documents Required for Claim (India)**:
• Valid **Motor Insurance Policy** document (own damage + third party)
• **Vehicle Registration Certificate (RC)** — original or DigiLocker copy
• **Driving Licence** of the person driving at the time of incident
• **FIR / Police Report** — mandatory for theft, severe accident, or hit-and-run
• **Claim Form** — filled and signed (Form 29 for third-party claims)
• **Repair Estimate** from an authorised / network garage
• **Photographs** of damage (already captured via AI tool own damage scan)
• **Aadhaar Card / PAN Card** for identity verification
• **Bank details** (account number, IFSC code) for NEFT payout
• **Cancelled cheque** — required for reimbursement claims""",

    "time": """**Processing Timeline**:
• AI assessment: **Instant**
• Claim registration: **Same day**
• Adjuster review: **2–3 business days**
• Approval decision: **5–7 working days**
• Payout transfer: **3–5 working days after approval**
• Total: approximately **2 weeks** end-to-end""",

    "deductible": """**Deductibles and Payouts (Indian Motor Insurance)**:

**Compulsory Deductible (as per IRDAI guidelines):**
• Private Cars ≤ 1500cc: **₹1,000**
• Private Cars > 1500cc: **₹2,000**

**Voluntary Excess (optional, reduces premium):**
• ₹500 / ₹1,000 / ₹2,000 / ₹5,000 / ₹7,500 / ₹15,000

**Typical Repair Costs in India:**
• Minor scratch / scuff: **₹500 – ₹3,000**
• Dent / panel damage: **₹3,000 – ₹15,000**
• Major body damage: **₹15,000 – ₹50,000**
• Heavy collision / totalled: **₹50,000 – ₹2,00,000**

Net Payout = Repair Cost − Compulsory Deductible − Voluntary Excess − Depreciation""",

    "appeal": """**Appealing a Decision**:
If your claim is rejected or partially approved, you may:
1. Request a formal re-evaluation within **30 days** of the decision.
2. Submit additional photographs or independent repair estimates.
3. Contact our grievance redressal officer at **claims@drivesure.ai**.
4. Escalate to the IRDAI Insurance Ombudsman if unresolved after 30 days.""",

    "coverage": """**Indian Motor Insurance Coverage (IRDAI)**:

**Comprehensive Policy Covers:**
✓ Own Damage (OD) — collision, overturn, falling objects
✓ Natural calamities — flood, cyclone, earthquake, fire, lightning
✓ Theft, burglary, housebreaking
✓ Third-party liability (mandatory by Motor Vehicles Act)
✓ Personal accident cover for owner-driver (₹15 lakh)
✓ Towing charges up to ₹1,500
✓ Roadside assistance (add-on)

**Not Covered:**
✗ Mechanical / electrical breakdown
✗ Normal wear and tear, depreciation beyond schedule
✗ Damage due to driving under the influence or invalid licence
✗ War, nuclear perils, mutiny
✗ Consequential loss (business loss, daily wages)
✗ Tyres and tubes (unless vehicle is damaged simultaneously)

**No Claim Bonus (NCB) — Discount for claim-free years:**
• 1 year: 20% • 2 years: 25% • 3 years: 35%
• 4 years: 45% • 5+ years: 50%

**IRDAI Depreciation Schedule:**
• Rubber/plastic parts: 50% • Fibre/glass: 30%
• Metal body: 0% (1st year) → 5–50% over age""",

    "status": """**Checking Claim Status**:
You can track your claim status by:
• Sharing your **Claim ID** in this chat
• Calling our helpline: **1800-XXX-XXXX** (toll-free)
• Emailing: **status@drivesure.ai**
• WhatsApp: **+91-98XXX-XXXXX**""",

    "cancel": """**Cancelling a Claim**:
You can cancel a pending claim within **48 hours** of submission.
After that, cancellation requires claims manager approval.
To cancel, share your Claim ID and write **cancel claim**.""",

    "payout": """**Payout Methods (Indian Insurance)**:

**Cashless Claim (at network garage):**
• Insurer pays the garage directly — **zero out-of-pocket**
• Must use an authorised network workshop
• Approval via surveyor within **2–4 hours**

**Reimbursement Claim (at any garage):**
• You pay upfront, submit bills for reimbursement
• Payout via **NEFT / IMPS** — **3–5 working days** after approval
• Payout via **cheque** — **7–10 days** to registered address
• **UPI** — for amounts up to ₹1,00,000 (near-instant after approval)

**Claim Limits:**
• Insured Declared Value (IDV) is the maximum payout
• Depreciation is deducted on parts as per IRDAI schedule
• NCB (No Claim Bonus) is forfeited if a claim is filed""",
}

# ─── Keywords → FAQ topic mapping ────────────────────────────────────────────
FAQ_KEYWORDS = {
    "process":    ["process", "how", "steps", "procedure", "start", "begin", "file"],
    "documents":  ["document", "papers", "required", "needed", "submit", "proof"],
    "time":       ["time", "long", "days", "when", "duration", "fast", "quick", "timeline"],
    "deductible": ["deductible", "excess", "payout", "amount", "pay", "money", "net"],
    "appeal":     ["appeal", "reject", "denied", "dispute", "challenge", "unfair"],
    "coverage":   ["cover", "covered", "not covered", "eligible", "what", "include"],
    "status":     ["status", "track", "where", "check", "update", "progress"],
    "cancel":     ["cancel", "withdraw", "stop", "drop"],
    "payout":     ["payout", "transfer", "neft", "bank", "receive", "upi", "cheque"],
}

# ─── Session helpers ───────────────────────────────────────────────────────────
def _get_session(session_id: str) -> dict:
    if session_id not in _SESSIONS:
        db_session = _load_session_from_db(session_id)
        if db_session:
            _SESSIONS[session_id] = db_session
        else:
            _SESSIONS[session_id] = {
                "state":   STATE_GREETING,
                "history": [],
                "claim":   {},
                "claim_id": None,
            }
            _save_session_to_db(session_id, _SESSIONS[session_id])
    return _SESSIONS[session_id]

def _add_history(session: dict, role: str, text: str):
    session["history"].append({
        "role": role,
        "text": text,
        "time": datetime.now().strftime("%I:%M %p")
    })
    for sid, s in _SESSIONS.items():
        if s is session:
            _save_session_to_db(sid, session)
            break

def _detect_faq(text: str) -> Optional[str]:
    text_lower = text.lower()
    for topic, keywords in FAQ_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return None

def _detect_intent(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["new claim", "file claim", "start claim", "register", "submit claim"]):
        return "new_claim"
    if any(w in text_lower for w in ["faq", "help", "question", "info", "information"]):
        return "faq"
    if any(w in text_lower for w in ["hi", "hello", "hey", "hii", "namaste", "good morning", "good evening"]):
        return "greet"
    if any(w in text_lower for w in ["bye", "exit", "quit", "done", "thank"]):
        return "bye"
    return "unknown"

def _generate_claim_id() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    uid      = uuid.uuid4().hex[:6].upper()
    return f"CLM-{date_str}-{uid}"

def compute_coverage_verdict(claim: dict) -> tuple[str, str]:
    """
    Compute the coverage verdict and estimated claim payout based on policy details and incident.
    """
    policy_type = claim.get("policy_type", "Comprehensive").strip()
    is_moving = claim.get("is_moving", "moving").strip().lower() == "moving"
    collision_type = claim.get("collision_type", "collision").strip().lower()
    
    # Parse deductible
    deductible_raw = claim.get("deductible", "0")
    digits = re.sub(r"\D", "", deductible_raw)
    deductible = int(digits) if digits else 1000  # Default compulsory excess if not known
    
    # Get AI damage scan cost range
    cost_range = claim.get("cost_range_inr", "₹0")
    costs = [int(x.replace(",", "")) for x in re.findall(r"₹?([0-9,]+)", cost_range)]
    avg_cost = sum(costs) // len(costs) if costs else 0
    
    verdict = ""
    payout_note = ""
    
    if "third party" in policy_type.lower():
        verdict = "Claim Rejected (Own Damage Not Covered)"
        payout_note = (
            "**Verdict:** Own damage is self-pay.\n"
            "**Reason:** A 'Third Party Only' policy covers liabilities for other vehicles or property, but does not cover own-damage to your vehicle. You will need to settle repair bills directly."
        )
    elif "zero dep" in policy_type.lower() or "invoice" in policy_type.lower():
        estimated_payout = max(0, avg_cost - deductible)
        verdict = "Claim Approved (Zero Depreciation Coverage)"
        payout_note = (
            f"**Verdict:** Full coverage approved.\n"
            f"**Compulsory Deductible:** ₹{deductible:,}\n"
            f"**Estimated AI Repair Cost:** {cost_range}\n"
            f"**Estimated Payout:** ₹{estimated_payout:,} (Zero-depreciation add-on covers full parts replacement without depreciation cuts)."
        )
    else:  # Comprehensive
        estimated_payout = max(0, avg_cost - deductible)
        
        if "theft" in collision_type:
            verdict = "Claim Pre-Approved (Comprehensive Theft Coverage)"
            payout_note = (
                f"**Verdict:** Theft claim applies.\n"
                f"**Required Action:** You must submit a certified copy of the First Information Report (FIR) filed with the police and the 'Non-Traceable Certificate'.\n"
                f"**Estimated Payout:** Up to the Insured Declared Value (IDV) minus deductible ₹{deductible:,}."
            )
        elif not is_moving and "vehicle" in collision_type:
            verdict = "Claim Route Suggestion: Third Party Liability Claim"
            payout_note = (
                f"**Verdict:** Since your vehicle was parked and hit by another vehicle, you can file a claim against the fault vehicle's Third Party Insurance (Self-Pay: ₹0).\n"
                f"**Alternative:** You can claim under your own Comprehensive policy (Estimated Payout: ₹{estimated_payout:,} minus deductible ₹{deductible:,}, but this will forfeit your No Claim Bonus)."
            )
        elif "windshield" in collision_type or "glass" in collision_type:
            verdict = "Windshield/Glass Claim Approved"
            payout_note = (
                f"**Verdict:** Covered under comprehensive own damage.\n"
                f"**Note:** Glass claims often have zero deductible (no compulsory excess) and do not affect your No Claim Bonus (NCB) in many add-on policies!"
            )
        elif "calamity" in collision_type or "flood" in collision_type or "fire" in collision_type or "weather" in collision_type or "nature" in collision_type:
            verdict = "Calamity Claim Approved"
            payout_note = (
                f"**Verdict:** Own damage covered under Comprehensive policy for acts of God.\n"
                f"**Estimated Payout:** ₹{estimated_payout:,} (Average repair cost minus deductible ₹{deductible:,} and standard depreciation on parts)."
            )
        else: # Standard moving collision / other
            verdict = "Own Damage Claim Approved"
            payout_note = (
                f"**Verdict:** Collision own damage covered.\n"
                f"**Estimated Payout:** ₹{estimated_payout:,} (Average repair cost minus deductible ₹{deductible:,} and standard depreciation on parts)."
            )
            
    return verdict, payout_note

def _format_claim_summary(claim: dict, claim_id: str) -> str:
    return f"""**Claim Successfully Registered!**

━━━━━━━━━━━━━━━━━━━━━━
**Claim ID**: `{claim_id}`
━━━━━━━━━━━━━━━━━━━━━━
Name          : {claim.get("name", "—")}
Email         : {claim.get("email", "—")}
Phone         : {claim.get("phone", "—")}
Policy Number : {claim.get("policy_id", "—")}
Incident Date : {claim.get("incident_date", "—")}
Description   : {claim.get("incident_desc", "—")}
Policy Type   : {claim.get("policy_type", "—")}
Verdict       : {claim.get("verdict", "—")}
━━━━━━━━━━━━━━━━━━━━━━

**Next Steps**:
• Save your Claim ID: **{claim_id}**
• Our adjuster will contact you within **2–3 business days** to arrange physical or digital verification.
• You can track status by sharing your Claim ID in this chat.

Thank you for using DriveSure AI."""

# ─── Main chat processor ──────────────────────────────────────────────────────
def process_message(session_id: str, user_text: str, detection_context: dict = None) -> tuple[str, list]:
    """
    Process a user message and return (bot_reply, history).
    Wraps _process_message_impl with error handling.
    """
    try:
        reply, history = _process_message_impl(session_id, user_text, detection_context)
        session = _get_session(session_id)
        _save_session_to_db(session_id, session)
        return reply, history
    except Exception as e:
        session = _get_session(session_id)
        reply = f"Something went wrong: {str(e)}. Please type **reset** to start over."
        _add_history(session, "bot", reply)
        _save_session_to_db(session_id, session)
        return reply, session["history"]

def _process_message_impl(session_id: str, user_text: str, detection_context: dict = None) -> tuple[str, list]:
    session  = _get_session(session_id)
    state    = session["state"]
    claim    = session["claim"]
    text     = user_text.strip()
    text_low = text.lower()

    _add_history(session, "user", text)

    # If AI detection result is passed, store it in claim
    if detection_context:
        claim.update({
            "severity":      detection_context.get("severity", "Unknown"),
            "damage_pct":    detection_context.get("damage_pct", 0),
            "cost_range_inr":detection_context.get("cost_range_inr", "N/A"),
        })

    # ── Global shortcuts ──────────────────────────────────────────────────────
    if text_low in ["reset", "restart", "clear"]:
        _SESSIONS[session_id] = {
            "state":    STATE_GREETING,
            "history":  [],
            "claim":    {},
            "claim_id": None,
        }
        session = _SESSIONS[session_id]
        reply = "Session reset. " + _greeting_message()
        _add_history(session, "bot", reply)
        return reply, session["history"]

    # ── State machine ─────────────────────────────────────────────────────────

    # GREETING / IDLE — entry point
    if state in [STATE_GREETING, STATE_IDLE]:
        intent = _detect_intent(text)

        if intent == "greet":
            reply = _greeting_message()

        elif intent == "new_claim":
            session["state"] = STATE_COLLECT_NAME
            reply = ("Let's register your insurance claim.\n\n"
                     "I will guide you through a few quick steps.\n\n"
                     "**Step 1/10** — What is your **full name**?")

        elif intent == "bye":
            reply = "Thank you for using DriveSure AI. Drive safe."

        else:
            # Check FAQ
            topic = _detect_faq(text)
            if topic:
                reply = FAQ_KB[topic]
            else:
                reply = _greeting_message()

    # COLLECT NAME
    elif state == STATE_COLLECT_NAME:
        if len(text) < 2:
            reply = "Please enter your full name (at least 2 characters)."
        else:
            claim["name"] = text.title()
            session["state"] = STATE_COLLECT_POLICY
            reply = (f"Hello, **{claim['name']}**.\n\n"
                     "**Step 2/10** — Please enter your **Policy Number**.\n"
                     "_(e.g., POL-2024-XXXXXX or as shown on your policy document)_")

    # COLLECT POLICY
    elif state == STATE_COLLECT_POLICY:
        if len(text) < 4:
            reply = "Please enter a valid policy number."
        else:
            claim["policy_id"] = text.upper()
            session["state"] = STATE_COLLECT_EMAIL
            reply = ("Policy number saved.\n\n"
                     "**Step 3/10** — What is your **email address**?")

    # COLLECT EMAIL
    elif state == STATE_COLLECT_EMAIL:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|in|org|net|co|edu|gov|info|biz|me|ai)$"
        if not re.match(email_regex, text):
            reply = "Please enter a valid email address (e.g. name@example.com)."
        else:
            claim["email"] = text.lower()
            session["state"] = STATE_COLLECT_PHONE
            reply = ("Email saved.\n\n"
                     "**Step 4/10** — What is your **mobile number**? _(10-digit Indian number)_")

    # COLLECT PHONE
    elif state == STATE_COLLECT_PHONE:
        digits = re.sub(r"\D", "", text)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]
            
        if len(digits) != 10:
            reply = "Please enter a valid 10-digit mobile number."
        else:
            claim["phone"] = digits
            session["state"] = STATE_COLLECT_DATE
            reply = ("Phone number saved.\n\n"
                     "**Step 5/10** — When did the incident occur?\n"
                     "_(Enter date as DD/MM/YYYY or describe e.g., 'yesterday', '20 May 2026')_")

    # COLLECT DATE
    elif state == STATE_COLLECT_DATE:
        if len(text) < 3:
            reply = "Please provide the incident date."
        else:
            claim["incident_date"] = text
            session["state"] = STATE_COLLECT_INCIDENT_DESC
            reply = ("Date noted.\n\n"
                     "**Step 6/10** — Please describe **what happened to the vehicle** in detail.\n"
                     "_(e.g., 'A vehicle crashed into my front bumper at a red light', or 'My car was damaged in a storm/flood')_")

    # COLLECT INCIDENT DESC
    elif state == STATE_COLLECT_INCIDENT_DESC:
        if len(text) < 3:
            reply = "Please provide a description of what happened."
        else:
            claim["incident_desc"] = text
            session["state"] = STATE_COLLECT_MOVING_PARKED
            reply = ("Incident description recorded.\n\n"
                     "**Step 7/10** — Was the vehicle **moving or parked** when this occurred?\n\n"
                     "1. Moving\n"
                     "2. Parked\n\n"
                     "_(Please type the number or write moving/parked)_")

    # COLLECT MOVING OR PARKED
    elif state == STATE_COLLECT_MOVING_PARKED:
        if text.strip() == "1" or "moving" in text_low:
            claim["is_moving"] = "moving"
            session["state"] = STATE_COLLECT_COLLISION_TYPE
            reply = ("Details recorded.\n\n"
                     "**Step 8/10** — What type of event was it?\n\n"
                     "1. Collision with another vehicle or object\n"
                     "2. Non-collision event (theft, weather, flood, fire, animal collision, etc.)\n"
                     "3. Windshield/glass damage only\n\n"
                     "_(Please type the number or write the category)_")
        elif text.strip() == "2" or "parked" in text_low:
            claim["is_moving"] = "parked"
            session["state"] = STATE_COLLECT_COLLISION_TYPE
            reply = ("Details recorded.\n\n"
                     "**Step 8/10** — What type of event was it?\n\n"
                     "1. Collision with another vehicle or object\n"
                     "2. Non-collision event (theft, weather, flood, fire, animal collision, etc.)\n"
                     "3. Windshield/glass damage only\n\n"
                     "_(Please type the number or write the category)_")
        else:
            reply = ("Please select a valid option:\n"
                     "1. Moving\n"
                     "2. Parked\n\n"
                     "Please type 1 or 2, or write 'moving' or 'parked'.")

    # COLLECT COLLISION TYPE
    elif state == STATE_COLLECT_COLLISION_TYPE:
        if text.strip() == "1" or "collision" in text_low:
            claim["collision_type"] = "collision"
            session["state"] = STATE_COLLECT_POLICY_TYPE
            reply = ("Event type recorded.\n\n"
                     "**Step 9/10** — What type of insurance policy do you hold for this vehicle?\n\n"
                     "1. Third Party Only (TP)\n"
                     "2. Comprehensive (OD + TP)\n"
                     "3. Zero Depreciation (Zero Dep)\n\n"
                     "_(Please select the option or write the policy type)_")
        elif text.strip() == "2" or "non" in text_low or "theft" in text_low or "weather" in text_low or "flood" in text_low or "fire" in text_low or "animal" in text_low:
            claim["collision_type"] = "non-collision"
            session["state"] = STATE_COLLECT_POLICY_TYPE
            reply = ("Event type recorded.\n\n"
                     "**Step 9/10** — What type of insurance policy do you hold for this vehicle?\n\n"
                     "1. Third Party Only (TP)\n"
                     "2. Comprehensive (OD + TP)\n"
                     "3. Zero Depreciation (Zero Dep)\n\n"
                     "_(Please select the option or write the policy type)_")
        elif text.strip() == "3" or "glass" in text_low or "windshield" in text_low:
            claim["collision_type"] = "glass/windshield"
            session["state"] = STATE_COLLECT_POLICY_TYPE
            reply = ("Event type recorded.\n\n"
                     "**Step 9/10** — What type of insurance policy do you hold for this vehicle?\n\n"
                     "1. Third Party Only (TP)\n"
                     "2. Comprehensive (OD + TP)\n"
                     "3. Zero Depreciation (Zero Dep)\n\n"
                     "_(Please select the option or write the policy type)_")
        else:
            reply = ("Please select a valid option:\n"
                     "1. Collision with another vehicle or object\n"
                     "2. Non-collision event\n"
                     "3. Windshield/glass damage only\n\n"
                     "Please type 1, 2, or 3, or write the category.")

    # COLLECT POLICY TYPE
    elif state == STATE_COLLECT_POLICY_TYPE:
        if text.strip() == "1" or "third" in text_low or "tp" in text_low:
            claim["policy_type"] = "Third Party Only"
            session["state"] = STATE_COLLECT_DEDUCTIBLE
            reply = ("Policy type recorded.\n\n"
                     "**Step 10/10** — What is your **compulsory excess / deductible** amount if known?\n\n"
                     "_(e.g., ₹1,000, ₹2,000 for standard IRDAI cars. Type 'not known' or write 'skip' to use standard ₹1,000)_")
        elif text.strip() == "2" or "comprehensive" in text_low:
            claim["policy_type"] = "Comprehensive"
            session["state"] = STATE_COLLECT_DEDUCTIBLE
            reply = ("Policy type recorded.\n\n"
                     "**Step 10/10** — What is your **compulsory excess / deductible** amount if known?\n\n"
                     "_(e.g., ₹1,000, ₹2,000 for standard IRDAI cars. Type 'not known' or write 'skip' to use standard ₹1,000)_")
        elif text.strip() == "3" or "zero" in text_low or "dep" in text_low:
            claim["policy_type"] = "Zero Depreciation"
            session["state"] = STATE_COLLECT_DEDUCTIBLE
            reply = ("Policy type recorded.\n\n"
                     "**Step 10/10** — What is your **compulsory excess / deductible** amount if known?\n\n"
                     "_(e.g., ₹1,000, ₹2,000 for standard IRDAI cars. Type 'not known' or write 'skip' to use standard ₹1,000)_")
        else:
            reply = ("Please select a valid policy type:\n"
                     "1. Third Party Only (TP)\n"
                     "2. Comprehensive (OD + TP)\n"
                     "3. Zero Depreciation (Zero Dep)\n\n"
                     "Please type 1, 2, or 3, or write your policy type.")

    # COLLECT DEDUCTIBLE
    elif state == STATE_COLLECT_DEDUCTIBLE:
        if text_low in ["skip", "none", "not known", "no", "na", "n/a", "unknown"]:
            claim["deductible"] = "₹1,000 (Default)"
        else:
            claim["deductible"] = text.strip()
            
        session["state"] = STATE_CONFIRM
        
        # Compute coverage verdict and payout estimate
        verdict, payout_note = compute_coverage_verdict(claim)
        claim["verdict"] = verdict
        claim["payout_note"] = payout_note
        
        sev_line = ""
        if claim.get("severity"):
            sev_line = (f"\nAI Scan Severity: {claim['severity']}\n"
                        f"Damage Area     : {claim.get('damage_pct', 'N/A')}%\n"
                        f"AI Cost Range   : {claim.get('cost_range_inr', 'N/A')}")
            
        reply = f"""**Please review your claim details:**

━━━━━━━━━━━━━━━━━━━━━━
Name          : {claim.get("name")}
Email         : {claim.get("email")}
Phone         : {claim.get("phone")}
Policy Number : {claim.get("policy_id")}
Incident Date : {claim.get("incident_date")}
Description   : {claim.get("incident_desc")}
Vehicle State : {claim.get("is_moving", "unknown").title()}
Event Type    : {claim.get("collision_type", "unknown").title()}
Policy Type   : {claim.get("policy_type")}
Deductible    : {claim.get("deductible")}{sev_line}
━━━━━━━━━━━━━━━━━━━━━━

**Coverage Analysis & Verdict:**
### {verdict}
{payout_note}

━━━━━━━━━━━━━━━━━━━━━━

Type **confirm** to submit your claim, or **edit** to start over."""

    # CONFIRM
    elif state == STATE_CONFIRM:
        if "confirm" in text_low or "yes" in text_low or "submit" in text_low or "ok" in text_low:
            claim_id = _generate_claim_id()
            session["claim_id"] = claim_id
            session["state"] = STATE_SUBMITTED
            reply = _format_claim_summary(claim, claim_id)
        elif "edit" in text_low or "no" in text_low or "change" in text_low:
            session["state"] = STATE_COLLECT_NAME
            session["claim"] = {}
            reply = ("Let's start over. I will collect your details again.\n\n"
                     "**Step 1/10** — What is your **full name**?")
        else:
            reply = "Please type **confirm** to submit or **edit** to start over."

    # SUBMITTED — allow status checks and FAQ
    elif state == STATE_SUBMITTED:
        topic = _detect_faq(text)
        if topic:
            reply = FAQ_KB[topic]
        elif "status" in text_low or "update" in text_low:
            cid = session.get("claim_id", "Unknown")
            reply = (f"Your claim **{cid}** is currently under review.\n"
                     "Our adjuster will contact you within 2–3 business days.")
        elif intent_new_claim(text_low):
            session["state"] = STATE_COLLECT_NAME
            session["claim"] = {}
            session["claim_id"] = None
            reply = ("Starting a new claim.\n\n"
                     "**Step 1/10** — What is your **full name**?")
        else:
            cid = session.get("claim_id", "your claim")
            reply = (f"Your claim **{cid}** has been registered.\n\n"
                     "Type **status** to check progress, or ask me any insurance question.")
    else:
        reply = _greeting_message()

    _add_history(session, "bot", reply)
    return reply, session["history"]

def intent_new_claim(text_low: str) -> bool:
    return any(w in text_low for w in ["new claim", "another claim", "file claim", "start claim"])

def _greeting_message() -> str:
    return """Welcome to DriveSure AI — Claims Management Assistant.

I can help you with:
• **File a new claim** — write "new claim"
• **FAQs** — ask about process, documents, timelines, or coverage
• **Claim status** — share your Claim ID

What would you like to do today?"""

def get_session_claim(session_id: str) -> dict:
    """Return the current claim data for a session (used by app.py)."""
    return _get_session(session_id).get("claim", {})

def get_session_history(session_id: str) -> list:
    """Return chat history for a session."""
    return _get_session(session_id).get("history", [])

def reset_session(session_id: str):
    """Clear a session completely."""
    if session_id in _SESSIONS:
        del _SESSIONS[session_id]
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_storage.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[Database Error] Failed to delete session: {e}")
