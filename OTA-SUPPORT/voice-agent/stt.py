"""
stt.py  ──  Speech-to-Text (STT)
Converts audio input into text using the Groq Whisper API.
Supports:
  • File path  → transcribe a .wav / .mp3 / .m4a file
  • Microphone → record N seconds then transcribe (requires pyaudio)
"""

import os
import io
import wave
import tempfile
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STT_MODEL    = "whisper-large-v3"          # best Groq Whisper model
LANGUAGE     = "en"                         # change to "ar", "fr" etc. if needed

client = Groq(api_key=GROQ_API_KEY)


# ── Transcribe an audio file ──────────────────────────────
def transcribe_file(file_path: str) -> str:
    """
    Transcribe any audio file (wav, mp3, m4a, ogg, flac).

    Args:
        file_path: absolute or relative path to the audio file

    Returns:
        Transcribed text string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    print(f"  🎙  Transcribing: {file_path}")

    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model    = STT_MODEL,
            file     = f,
            language = LANGUAGE
        )

    text = transcription.text.strip()
    print(f"  ✓ STT result: '{text[:80]}'")
    return text


# ── Transcribe raw PCM bytes (from live capture) ──────────
def transcribe_bytes(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe raw PCM16 bytes by wrapping them in a WAV container
    and sending to Groq Whisper.

    Args:
        audio_bytes : raw PCM16 audio data
        sample_rate : sample rate in Hz (default 16000)

    Returns:
        Transcribed text string
    """
    # Wrap PCM in a proper WAV container
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)        # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)
    wav_buffer.seek(0)

    # Write to temp file (Groq SDK needs a file-like object with a name)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_buffer.read())
        tmp_path = tmp.name

    try:
        return transcribe_file(tmp_path)
    finally:
        os.unlink(tmp_path)


# ── Record from microphone then transcribe ────────────────
def record_and_transcribe(duration_seconds: int = 5, sample_rate: int = 16000) -> str:
    """
    Record audio from the default microphone for `duration_seconds`
    then return the transcription.

    Requires: pip install pyaudio
    """
    try:
        import pyaudio
    except ImportError:
        raise ImportError("pyaudio is required for microphone capture. Run: pip install pyaudio")

    chunk      = 1024
    fmt        = pyaudio.paInt16
    channels   = 1

    pa     = pyaudio.PyAudio()
    stream = pa.open(
        format           = fmt,
        channels         = channels,
        rate             = sample_rate,
        input            = True,
        frames_per_buffer= chunk
    )

    print(f"  🎤 Recording for {duration_seconds}s... speak now")
    frames = []
    for _ in range(int(sample_rate / chunk * duration_seconds)):
        frames.append(stream.read(chunk))

    stream.stop_stream()
    stream.close()
    pa.terminate()
    print("  ✓ Recording complete")

    audio_bytes = b"".join(frames)
    return transcribe_bytes(audio_bytes, sample_rate)


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # python stt.py path/to/file.wav
        result = transcribe_file(sys.argv[1])
        print(f"\nTranscription:\n{result}\n")
    else:
        # python stt.py  →  record 5 seconds from mic
        result = record_and_transcribe(duration_seconds=5)
        print(f"\nTranscription:\n{result}\n")