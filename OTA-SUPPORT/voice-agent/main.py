"""
main.py  ──  AntiGravity Voice Agent — Entry Point
Runs the full pipeline for one call or a live interactive session:

  Microphone / audio file
        ↓  STT (Whisper via Groq)
  Customer text
        ↓  Brain → Router → KB → Groq LLM
  Agent reply text
        ↓  TTS (gTTS)
  Spoken response
        ↓  Reports + Analytics
  DB saved, alerts fired if needed

Usage:
  python main.py                      # interactive mic session
  python main.py --text               # type instead of speak (no mic needed)
  python main.py --file audio.wav     # transcribe a file then process
  python main.py --api                # start FastAPI server
"""

import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from agent.brain        import handle_customer_input
from agent.resolution   import process_resolution
from analytics.monitor  import check_and_alert
from db.models          import init_db
from db.reports         import generate_call_id, save_call_report


# ── Single-turn pipeline ───────────────────────────────────
def run_call(customer_input: str, customer_name: str = "Unknown", speak_reply: bool = True):
    """
    Full pipeline for one customer message.
    """
    call_id = generate_call_id()
    print(f"\n{'='*55}")
    print(f"  Call ID  : {call_id}")
    print(f"  Customer : {customer_name}")
    print(f"  Input    : {customer_input}")
    print(f"{'='*55}")

    # 1. Brain
    result = handle_customer_input(
        customer_input = customer_input,
        customer_name  = customer_name
    )

    # 2. Resolution
    res = process_resolution(
        call_id        = call_id,
        customer_name  = customer_name,
        customer_input = customer_input,
        kb_answer      = result["kb_answer"],
        agent_reply    = result["reply"],
        intent         = result["intent"],
        issue_category = result["issue_category"],
        resolved       = result["resolved"]
    )

    # 3. Save to DB
    save_call_report(
        call_id        = call_id,
        intent         = result["intent"],
        issue_category = result["issue_category"],
        transcript     = f"Customer: {customer_input}\nAgent: {result['reply']}",
        resolution     = res["resolution_note"],
        resolved       = result["resolved"],
        customer_name  = customer_name
    )

    # 4. Analytics / alerts
    check_and_alert(
        issue_category     = result["issue_category"],
        escalation_message = res["escalation_message"]
    )

    # 5. Speak the reply
    if speak_reply:
        try:
            from tts import speak
            speak(result["reply"])
        except Exception as e:
            print(f"  ⚠ TTS failed ({e}), printing instead")
            print(f"\n🤖 Agent: {result['reply']}\n")
    else:
        print(f"\n🤖 Agent: {result['reply']}\n")

    return result


# ── Interactive text session ───────────────────────────────
def run_text_session():
    print("\n" + "="*55)
    print("  AntiGravity Voice Agent — Text Mode")
    print("  Type your message and press Enter.")
    print("  Type 'quit' or 'exit' to end the session.")
    print("="*55)

    customer_name = input("\nYour name (or press Enter for Anonymous): ").strip() or "Unknown"

    while True:
        try:
            user_input = input(f"\n[{customer_name}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "bye", "goodbye"}:
            print("\n🤖 Agent: Thank you for contacting AntiGravity. Have a great day!")
            break

        run_call(customer_input=user_input, customer_name=customer_name, speak_reply=False)


# ── Interactive voice session ──────────────────────────────
def run_voice_session():
    from stt import record_and_transcribe
    from tts import speak

    print("\n" + "="*55)
    print("  AntiGravity Voice Agent — Voice Mode")
    print("  Press Ctrl+C to end the session.")
    print("="*55)

    customer_name = "Voice Customer"
    speak("Welcome to AntiGravity support. How can I help you today?")

    while True:
        try:
            print("\n🎤 Listening... (5 seconds)")
            customer_input = record_and_transcribe(duration_seconds=5)

            if not customer_input.strip():
                speak("I'm sorry, I didn't catch that. Could you please repeat?")
                continue

            if any(w in customer_input.lower() for w in ["goodbye", "bye", "quit", "exit"]):
                speak("Thank you for calling AntiGravity. Have a wonderful day!")
                break

            run_call(customer_input=customer_input, customer_name=customer_name, speak_reply=True)

        except KeyboardInterrupt:
            print("\n\nSession ended.")
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            break


# ── Process a single audio file ────────────────────────────
def run_file(file_path: str):
    from stt import transcribe_file
    customer_input = transcribe_file(file_path)
    run_call(customer_input=customer_input, speak_reply=True)


# ── Start FastAPI server ───────────────────────────────────
def run_api():
    import uvicorn
    print("\n🚀 Starting AntiGravity API on http://0.0.0.0:8000")
    print("   Docs: http://localhost:8000/docs\n")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)


# ── CLI ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AntiGravity Voice Agent"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text",  action="store_true", help="Text input mode (no mic)")
    group.add_argument("--file",  type=str,            help="Path to audio file")
    group.add_argument("--api",   action="store_true", help="Start FastAPI server")
    args = parser.parse_args()

    # Ensure DB tables exist
    init_db()

    if args.api:
        run_api()
    elif args.text:
        run_text_session()
    elif args.file:
        run_file(args.file)
    else:
        # Default: voice mode
        try:
            run_voice_session()
        except ImportError:
            print("\n⚠  pyaudio not installed — falling back to text mode")
            print("   Install with: pip install pyaudio\n")
            run_text_session()


if __name__ == "__main__":
    main()