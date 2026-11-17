from db.models import SessionLocal, CallReport, RecurringAlert
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

THRESHOLD      = int(os.getenv("RECURRING_ISSUE_THRESHOLD", 5))
WINDOW_MINUTES = int(os.getenv("RECURRING_ISSUE_WINDOW_MINUTES", 120))


# ── Generate a unique call ID ──────────────────────────────
def generate_call_id() -> str:
    return str(uuid.uuid4())[:8].upper()  # e.g. "A3F9B2C1"


# ── Save a completed call to the database ─────────────────
def save_call_report(
    call_id:        str,
    intent:         str,
    issue_category: str,
    transcript:     str,
    resolution:     str,
    resolved:       bool,
    customer_name:  str = "Unknown"
):
    db = SessionLocal()
    try:
        report = CallReport(
            call_id        = call_id,
            customer_name  = customer_name,
            intent         = intent,
            issue_category = issue_category,
            transcript     = transcript,
            resolution     = resolution,
            resolved       = resolved,
            timestamp      = datetime.utcnow()
        )
        db.add(report)
        db.commit()
        print(f"✓ Call {call_id} saved to database")
        return report
    except Exception as e:
        db.rollback()
        print(f"✗ Failed to save call: {e}")
        return None
    finally:
        db.close()


# ── Get all calls within the last N minutes ───────────────
def get_recent_calls(minutes: int = WINDOW_MINUTES):
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        calls  = db.query(CallReport)\
                   .filter(CallReport.timestamp >= cutoff)\
                   .all()
        return calls
    finally:
        db.close()


# ── Count how many times an issue appeared recently ───────
def count_issue_occurrences(issue_category: str, minutes: int = WINDOW_MINUTES) -> int:
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        count  = db.query(CallReport)\
                   .filter(CallReport.issue_category == issue_category)\
                   .filter(CallReport.timestamp >= cutoff)\
                   .count()
        return count
    finally:
        db.close()


# ── Save a recurring alert when threshold is breached ─────
def save_recurring_alert(
    issue_category: str,
    occurrences:    int,
    report_summary: str
):
    db = SessionLocal()
    try:
        alert = RecurringAlert(
            issue_category = issue_category,
            occurrences    = occurrences,
            window_minutes = WINDOW_MINUTES,
            alert_sent_at  = datetime.utcnow(),
            report_summary = report_summary
        )
        db.add(alert)
        db.commit()
        print(f"✓ Alert saved for issue: {issue_category}")
        return alert
    except Exception as e:
        db.rollback()
        print(f"✗ Failed to save alert: {e}")
        return None
    finally:
        db.close()


# ── Get all unresolved calls ───────────────────────────────
def get_unresolved_calls():
    db = SessionLocal()
    try:
        return db.query(CallReport)\
                 .filter(CallReport.resolved == False)\
                 .all()
    finally:
        db.close()