"""
brain.py  ──  Central conversation engine
Receives transcribed text → classifies intent → queries KB → picks resolution
→ returns a reply + structured call metadata.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from agent.kb_chain import ask_knowledge_base
from agent.router   import classify_intent, classify_issue_category

load_dotenv()

GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", 0.3))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", 1024))


# ── LLM singleton ──────────────────────────────────────────
def get_llm():
    return ChatGroq(
        api_key     = GROQ_API_KEY,
        model_name  = GROQ_MODEL,
        temperature = GROQ_TEMPERATURE,
        max_tokens  = GROQ_MAX_TOKENS
    )


# ── Build a warm, natural reply from KB answer ─────────────
def generate_reply(customer_input: str, kb_answer: str, intent: str) -> str:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template("""
You are a friendly and professional voice agent for AntiGravity, a telecom company.
Your job is to speak naturally with customers, like a real human support agent.

Customer said: "{customer_input}"
Their intent: {intent}
Knowledge base answer: "{kb_answer}"

Instructions:
- Respond in 2-3 sentences maximum (this will be spoken aloud via TTS).
- Be warm, concise, and helpful.
- Do NOT mention "knowledge base" or "database".
- If the KB answer is empty or unhelpful, apologize and offer to escalate.
- Never make up policies or prices.

Your reply:
""")

    chain  = prompt | llm | StrOutputParser()
    return chain.invoke({
        "customer_input": customer_input,
        "kb_answer"     : kb_answer,
        "intent"        : intent
    })


# ── Decide if the call was resolved ───────────────────────
def was_resolved(kb_answer: str, reply: str) -> bool:
    """Heuristic: if the KB had an answer and reply doesn't ask to escalate."""
    escalation_keywords = ["escalate", "transfer", "sorry", "unable", "can't help"]
    combined = (kb_answer + " " + reply).lower()
    return bool(kb_answer.strip()) and not any(k in combined for k in escalation_keywords)


# ── Main entry point called by main.py ────────────────────
def handle_customer_input(
    customer_input: str,
    customer_name:  str = "Unknown",
    conversation_history: list = None
) -> dict:
    """
    Process one customer message end-to-end.

    Returns:
        {
            "reply"         : str,   # what to say back (feed to TTS)
            "intent"        : str,   # "inquiry" | "complaint" | "other"
            "issue_category": str,   # "billing" | "network" | "hardware" | "general"
            "kb_answer"     : str,   # raw KB result
            "resolved"      : bool
        }
    """
    print(f"\n── Brain processing: '{customer_input[:60]}...' ──")

    # 1. Classify
    intent         = classify_intent(customer_input)
    issue_category = classify_issue_category(customer_input)
    print(f"   intent={intent}  category={issue_category}")

    # 2. Retrieve from knowledge base
    try:
        kb_answer = ask_knowledge_base(customer_input)
    except Exception as e:
        print(f"   ✗ KB lookup failed: {e}")
        kb_answer = ""

    # 3. Generate natural reply
    try:
        reply = generate_reply(customer_input, kb_answer, intent)
    except Exception as e:
        print(f"   ✗ Reply generation failed: {e}")
        reply = "I'm sorry, I'm having trouble right now. Let me connect you with a human agent."

    # 4. Resolve flag
    resolved = was_resolved(kb_answer, reply)

    print(f"   resolved={resolved}")
    print(f"   reply='{reply[:80]}...'")

    return {
        "reply"         : reply,
        "intent"        : intent,
        "issue_category": issue_category,
        "kb_answer"     : kb_answer,
        "resolved"      : resolved
    }