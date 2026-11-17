"""
tts.py  ──  Text-to-Speech (TTS)
Converts agent reply text into spoken audio.
Uses gTTS (Google Text-to-Speech) — free, no API key needed.
Plays the audio immediately and optionally saves it.

Install: pip install gtts playsound
"""

import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

LANGUAGE     = os.getenv("TTS_LANGUAGE", "en")   # "ar", "fr", etc.
SLOW_SPEECH  = os.getenv("TTS_SLOW", "False").lower() == "true"
AUDIO_OUTPUT = os.getenv("TTS_OUTPUT_PATH", "")  # set to save audio files


# ── Speak text aloud ──────────────────────────────────────
def speak(text: str, save_path: str = None) -> str:
    """
    Convert `text` to speech and play it.

    Args:
        text      : the text to speak
        save_path : optional file path to save the .mp3 (e.g. "reply.mp3")

    Returns:
        Path to the generated audio file (temp or saved)
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise ImportError("gTTS is required. Run: pip install gtts")

    print(f"  🔊 TTS: '{text[:80]}{'...' if len(text) > 80 else ''}'")

    tts = gTTS(text=text, lang=LANGUAGE, slow=SLOW_SPEECH)

    # Determine output path
    if save_path:
        out_path = save_path
    elif AUDIO_OUTPUT:
        out_path = AUDIO_OUTPUT
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        out_path = tmp.name
        tmp.close()

    tts.save(out_path)
    print(f"  ✓ Audio saved: {out_path}")

    _play(out_path)
    return out_path


# ── Play an audio file ────────────────────────────────────
def _play(file_path: str) -> None:
    """
    Play an audio file. Tries playsound first, falls back to system commands.
    """
    # Try playsound
    try:
        from playsound import playsound
        playsound(file_path)
        return
    except Exception:
        pass

    # Try platform-specific fallbacks
    import platform
    system = platform.system()

    try:
        if system == "Windows":
            import winsound
            winsound.PlaySound(file_path, winsound.SND_FILENAME)
        elif system == "Darwin":  # macOS
            os.system(f"afplay '{file_path}'")
        else:                     # Linux
            os.system(f"mpg123 '{file_path}' 2>/dev/null || aplay '{file_path}' 2>/dev/null")
    except Exception as e:
        print(f"  ⚠ Could not play audio automatically: {e}")
        print(f"    → Audio saved at: {file_path}")


# ── Text-only mode (no audio device needed) ───────────────
def speak_text_only(text: str) -> None:
    """Print the reply without generating audio (useful for testing)."""
    print(f"\n🤖 Agent says: {text}\n")


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    test_text = "Hello! Welcome to AntiGravity support. How can I help you today?"
    speak(test_text)