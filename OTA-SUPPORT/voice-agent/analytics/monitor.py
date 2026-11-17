"""
monitor.py  ──  Analytics monitor & alert dispatcher
Runs after every call to:
  • Check if a recurring issue threshold has been breached
  • Send an email and/or Slack alert to the admin team
  • Save the alert to the database
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from dotenv import load_dotenv

from db.reports import (
    count_issue_occurrences,
    save_recurring_alert,
    get_unresolved_calls
)

load_dotenv()

# ── Config ─────────────────────────────────────────────────
THRESHOLD      = int(os.getenv("RECURRING_ISSUE_THRESHOLD", 5))
WINDOW_MINUTES = int(os.getenv("RECURRING_ISSUE_WINDOW_MINUTES", 120))

SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASSWORD  = os.getenv("SMTP_PASSWORD", "")

SLACK_WEBHOOK  = os.getenv("SLACK_WEBHOOK_URL", "")
DEBUG          = os.getenv("DEBUG", "False").lower() == "true"


# ── Email alert ────────────────────────────────────────────
def send_email_alert(subject: str, body: str, to_email: str = None) -> bool:
    to_email = to_email or SMTP_USER
    if not SMTP_USER or not SMTP_PASSWORD:
        print("  ⚠ Email not configured (SMTP_USER / SMTP_PASSWORD missing)")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"]    = SMTP_USER
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"  ✓ Email alert sent to {to_email}")
        return True
    except Exception as e:
        print(f"  ✗ Email failed: {e}")
        return False


# ── Slack alert ────────────────────────────────────────────
def send_slack_alert(message: str) -> bool:
    if not SLACK_WEBHOOK:
        print("  ⚠ Slack not configured (SLACK_WEBHOOK_URL missing)")
        return False

    try:
        resp = requests.post(
            SLACK_WEBHOOK,
            json    = {"text": message},
            timeout = 10
        )
        if resp.status_code == 200:
            print("  ✓ Slack alert sent")
            return True
        else:
            print(f"  ✗ Slack returned {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"  ✗ Slack failed: {e}")
        return False


# ── Build alert body ───────────────────────────────────────
def _build_alert_body(issue_category: str, occurrences: int) -> str:
    unresolved = get_unresolved_calls()
    unresolved_count = len(unresolved)

    return (
        f"⚠️  RECURRING ISSUE ALERT — AntiGravity Voice Agent\n"
        f"{'─' * 45}\n"
        f"Issue Category : {issue_category.upper()}\n"
        f"Occurrences    : {occurrences} times in the last {WINDOW_MINUTES} minutes\n"
        f"Threshold      : {THRESHOLD}\n"
        f"Unresolved calls (all categories): {unresolved_count}\n"
        f"{'─' * 45}\n"
        f"Please review the dashboard and take action.\n"
    )


# ── Core check — call this after every call ────────────────
def check_and_alert(issue_category: str, escalation_message: str = None) -> bool:
    """
    Checks if `issue_category` has exceeded THRESHOLD in the last WINDOW_MINUTES.
    If yes → sends email + Slack alert and saves to DB.

    Returns True if an alert was fired.
    """
    occurrences = count_issue_occurrences(issue_category)
    print(f"  📊 '{issue_category}' occurrences in last {WINDOW_MINUTES}min: {occurrences}/{THRESHOLD}")

    if occurrences < THRESHOLD:
        return False

    print(f"  🚨 Threshold breached for '{issue_category}'! Sending alerts...")

    body = _build_alert_body(issue_category, occurrences)

    # Append any escalation detail
    if escalation_message:
        body += f"\nLatest escalation:\n{escalation_message}"

    subject = f"[AntiGravity Alert] Recurring {issue_category} issues ({occurrences}x)"

    # Dispatch
    send_email_alert(subject, body)
    send_slack_alert(body)

    # Persist alert
    save_recurring_alert(
        issue_category = issue_category,
        occurrences    = occurrences,
        report_summary = body
    )

    return True


# ── Daily summary (optional, call via cron/scheduler) ─────
def send_daily_summary() -> None:
    """Sends a daily unresolved-call summary to the admin."""
    unresolved = get_unresolved_calls()
    if not unresolved:
        print("  ✓ No unresolved calls — no daily summary needed")
        return

    lines = [f"  • [{c.call_id}] {c.customer_name} — {c.issue_category}" for c in unresolved]
    body  = (
        f"📋 Daily Unresolved Calls Report — AntiGravity\n"
        f"{'─' * 45}\n"
        f"Total unresolved: {len(unresolved)}\n\n"
        + "\n".join(lines)
        + f"\n{'─' * 45}\n"
    )

    send_email_alert("[AntiGravity] Daily Unresolved Calls", body)
    send_slack_alert(body)
    print(f"  ✓ Daily summary sent ({len(unresolved)} unresolved calls)")


# ── Self-test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── Monitor self-test ─────────────────────")
    send_slack_alert("🧪 AntiGravity monitor test message")
    send_email_alert("AntiGravity test", "This is a test alert from monitor.py")
    print("─────────────────────────────────────────\n")