"""
app.py  ──  FastAPI REST API
Exposes the voice agent over HTTP so it can be integrated with any
telephony gateway (Twilio, Vonage, etc.) or tested via curl / Postman.

Endpoints:
  POST /call          — process a customer message end-to-end
  GET  /calls         — list recent calls
  GET  /calls/{id}    — get one call report
  GET  /health        — liveness check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from agent.brain       import handle_customer_input
from agent.resolution  import process_resolution
from analytics.monitor import check_and_alert
from db.models         import init_db, SessionLocal, CallReport
from db.reports        import (
    generate_call_id,
    save_call_report,
    get_recent_calls
)

# ── App setup ──────────────────────────────────────────────
app = FastAPI(
    title       = "AntiGravity Voice Agent API",
    description = "AI-powered telecom customer support",
    version     = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"]
)


# ── DB init on startup ────────────────────────────────────
@app.on_event("startup")
def startup_event():
    init_db()
    print("✓ Database ready")


# ── Request / Response models ─────────────────────────────
class CallRequest(BaseModel):
    customer_input: str
    customer_name : Optional[str] = "Unknown"


class CallResponse(BaseModel):
    call_id        : str
    reply          : str
    intent         : str
    issue_category : str
    resolved       : bool
    resolution_note: str
    needs_escalation: bool


# ── POST /call ────────────────────────────────────────────
@app.post("/call", response_model=CallResponse)
def handle_call(req: CallRequest):
    """Main endpoint — receives customer speech (as text) and returns agent reply."""

    call_id = generate_call_id()
    print(f"\n{'='*50}")
    print(f"Incoming call  : {call_id}")
    print(f"Customer       : {req.customer_name}")
    print(f"Input          : {req.customer_input[:80]}")

    # 1. Brain processes the input
    brain_result = handle_customer_input(
        customer_input = req.customer_input,
        customer_name  = req.customer_name
    )

    # 2. Resolution pipeline
    res = process_resolution(
        call_id        = call_id,
        customer_name  = req.customer_name,
        customer_input = req.customer_input,
        kb_answer      = brain_result["kb_answer"],
        agent_reply    = brain_result["reply"],
        intent         = brain_result["intent"],
        issue_category = brain_result["issue_category"],
        resolved       = brain_result["resolved"]
    )

    # 3. Save to DB
    save_call_report(
        call_id        = call_id,
        intent         = brain_result["intent"],
        issue_category = brain_result["issue_category"],
        transcript     = f"Customer: {req.customer_input}\nAgent: {brain_result['reply']}",
        resolution     = res["resolution_note"],
        resolved       = brain_result["resolved"],
        customer_name  = req.customer_name
    )

    # 4. Analytics check
    check_and_alert(
        issue_category    = brain_result["issue_category"],
        escalation_message = res["escalation_message"]
    )

    return CallResponse(
        call_id          = call_id,
        reply            = brain_result["reply"],
        intent           = brain_result["intent"],
        issue_category   = brain_result["issue_category"],
        resolved         = brain_result["resolved"],
        resolution_note  = res["resolution_note"],
        needs_escalation = res["needs_escalation"]
    )


# ── GET /calls ────────────────────────────────────────────
@app.get("/calls")
def list_calls(minutes: int = 120):
    """Return all calls from the last N minutes."""
    calls = get_recent_calls(minutes=minutes)
    return [
        {
            "call_id"       : c.call_id,
            "customer_name" : c.customer_name,
            "intent"        : c.intent,
            "issue_category": c.issue_category,
            "resolved"      : c.resolved,
            "timestamp"     : c.timestamp.isoformat()
        }
        for c in calls
    ]


# ── GET /calls/{call_id} ──────────────────────────────────
@app.get("/calls/{call_id}")
def get_call(call_id: str):
    """Return the full record for a single call."""
    db   = SessionLocal()
    call = db.query(CallReport).filter(CallReport.call_id == call_id).first()
    db.close()

    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")

    return {
        "call_id"       : call.call_id,
        "customer_name" : call.customer_name,
        "intent"        : call.intent,
        "issue_category": call.issue_category,
        "transcript"    : call.transcript,
        "resolution"    : call.resolution,
        "resolved"      : call.resolved,
        "timestamp"     : call.timestamp.isoformat()
    }


# ── GET /health ───────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "AntiGravity Voice Agent"}


# ── Run directly ──────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)