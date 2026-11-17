"""
resolution.py  ──  Post-call resolution actions
After brain.py produces a reply this module handles:
  • Deciding the resolution label/text to store in the DB
  • Escalation messaging when the AI couldn't resolve
  • Ticket-style follow-up notes
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", 0.3))
GROQ_MAX_TOKENS  = int(os.getenv("GROQ_MAX_TOKENS", 1024))


def _get_llm():
    return ChatGroq(
        api_key     = GROQ_API_KEY,
        model_name  = GROQ_MODEL,
        temperature = GROQ_TEMPERATURE,
        max_tokens  = GROQ_MAX_TOKENS
    )


# ── Summarise what happened in the call ───────────────────
def summarise_resolution(
    customer_input: str,
    kb_answer:      str,
    agent_reply:    str,
    resolved:       bool
) -> str:
    """
    Generate a short human-readable resolution note for the database.
    This goes into CallReport.resolution.
    """
    llm = _get_llm()

    status = "RESOLVED" if resolved else "UNRESOLVED – ESCALATION NEEDED"

    prompt = ChatPromptTemplate.from_template("""
Write a concise internal call-resolution note (2-3 sentences max) for a support ticket.

Status     : {status}
Customer   : "{customer_input}"
KB Answer  : "{kb_answer}"
Agent reply: "{agent_reply}"

Include:
- What the customer's problem was
- What information was provided
- Whether it was resolved or needs follow-up

Note:""")

    chain = prompt | _get_llm() | StrOutputParser()
    return chain.invoke({
        "status"        : status,
        "customer_input": customer_input,
        "kb_answer"     : kb_answer,
        "agent_reply"   : agent_reply
    }).strip()


# ── Escalation message (for unresolved calls) ─────────────
def build_escalation_message(
    call_id:        str,
    customer_name:  str,
    intent:         str,
    issue_category: str,
    transcript:     str
) -> str:
    """
    Returns a formatted escalation message ready to be sent via
    email or Slack (handled by monitor.py).
    """
    return (
        f"🚨 ESCALATION REQUIRED\n"
        f"{'─' * 40}\n"
        f"Call ID        : {call_id}\n"
        f"Customer       : {customer_name}\n"
        f"Intent         : {intent}\n"
        f"Issue Category : {issue_category}\n"
        f"{'─' * 40}\n"
        f"Transcript:\n{transcript}\n"
        f"{'─' * 40}\n"
        f"Action needed  : Please review and contact the customer.\n"
    )


# ── Full resolution pipeline (called by main.py) ──────────
def process_resolution(
    call_id:        str,
    customer_name:  str,
    customer_input: str,
    kb_answer:      str,
    agent_reply:    str,
    intent:         str,
    issue_category: str,
    resolved:       bool
) -> dict:
    """
    Runs all post-call resolution logic.

    Returns:
        {
            "resolution_note"      : str,
            "escalation_message"   : str | None,
            "needs_escalation"     : bool
        }
    """
    # 1. Always write a resolution note
    resolution_note = summarise_resolution(
        customer_input = customer_input,
        kb_answer      = kb_answer,
        agent_reply    = agent_reply,
        resolved       = resolved
    )

    # 2. Build escalation message only when unresolved
    escalation_message = None
    if not resolved:
        transcript = f"Customer: {customer_input}\nAgent: {agent_reply}"
        escalation_message = build_escalation_message(
            call_id        = call_id,
            customer_name  = customer_name,
            intent         = intent,
            issue_category = issue_category,
            transcript     = transcript
        )

    return {
        "resolution_note"   : resolution_note,
        "escalation_message": escalation_message,
        "needs_escalation"  : not resolved
    }