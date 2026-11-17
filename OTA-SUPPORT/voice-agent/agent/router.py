"""
router.py  ──  Intent & issue-category classifier
Uses Groq LLM to label incoming customer messages so the rest of the
pipeline (brain, reports, analytics) can act on structured data.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", 0.1))   # low temp for classification
GROQ_MAX_TOKENS  = int(os.getenv("GROQ_MAX_TOKENS", 1024))


def _get_llm():
    return ChatGroq(
        api_key     = GROQ_API_KEY,
        model_name  = GROQ_MODEL,
        temperature = GROQ_TEMPERATURE,
        max_tokens  = GROQ_MAX_TOKENS
    )


# ── Intent classifier ─────────────────────────────────────
def classify_intent(customer_input: str) -> str:
    """
    Returns one of: "inquiry" | "complaint" | "other"
    """
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_template("""
Classify the customer message below into exactly ONE of these intents:
- inquiry   : customer is asking a question or requesting information
- complaint : customer is unhappy, reporting a problem, or expressing frustration
- other     : anything that does not fit the above

Rules:
- Reply with ONLY the single word (inquiry / complaint / other).
- No punctuation, no explanation.

Customer message: "{text}"
Intent:""")

    chain  = prompt | llm | StrOutputParser()
    result = chain.invoke({"text": customer_input}).strip().lower()

    allowed = {"inquiry", "complaint", "other"}
    return result if result in allowed else "other"


# ── Issue-category classifier ─────────────────────────────
def classify_issue_category(customer_input: str) -> str:
    """
    Returns one of: "billing" | "network" | "hardware" | "account" | "general"
    """
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_template("""
Classify the customer message below into exactly ONE issue category:
- billing  : invoices, charges, payments, refunds, plans, pricing
- network  : internet speed, connectivity, outage, signal, coverage
- hardware : device, router, modem, SIM card, handset, equipment
- account  : login, password, registration, profile, subscription
- general  : anything that does not fit the above categories

Rules:
- Reply with ONLY the single word (billing / network / hardware / account / general).
- No punctuation, no explanation.

Customer message: "{text}"
Category:""")

    chain  = prompt | llm | StrOutputParser()
    result = chain.invoke({"text": customer_input}).strip().lower()

    allowed = {"billing", "network", "hardware", "account", "general"}
    return result if result in allowed else "general"


# ── Quick self-test ────────────────────────────────────────
if __name__ == "__main__":
    samples = [
        "My internet has been down for 3 days, this is unacceptable!",
        "What are your current data plans?",
        "I was charged twice on my last bill.",
        "How do I reset my router?",
        "I forgot my account password.",
    ]
    print("\n── Router self-test ──────────────────────")
    for s in samples:
        intent   = classify_intent(s)
        category = classify_issue_category(s)
        print(f"  [{intent:9}] [{category:8}]  {s[:55]}")
    print("─────────────────────────────────────────\n")