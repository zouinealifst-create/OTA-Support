# AntiGravity Voice Agent

AI-powered telecom customer support agent using **Groq (LLM + Whisper)**, **Gemini embeddings**, **Pinecone**, and **PostgreSQL**.

---

## Project Structure

```
voice-agent/
├── agent/
│   ├── brain.py          # Core conversation engine
│   ├── kb_chain.py       # RAG pipeline (Pinecone + Gemini + Groq)
│   ├── router.py         # Intent & category classifier
│   └── resolution.py     # Post-call resolution & escalation
├── analytics/
│   └── monitor.py        # Recurring-issue detection & alerts
├── api/
│   └── app.py            # FastAPI REST endpoints
├── db/
│   ├── models.py         # SQLAlchemy models (CallReport, RecurringAlert)
│   └── reports.py        # DB read/write helpers
├── knowledge_base/
│   └── documents/        # .txt files ingested into Pinecone
├── stt.py                # Speech-to-Text (Groq Whisper)
├── tts.py                # Text-to-Speech (gTTS)
├── main.py               # Entry point
├── .env                  # API keys & config (never commit this)
└── requirements.txt
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env` and fill in your keys (already done).

### 3. Set up PostgreSQL
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE antigravity_db;"

# Initialize tables
python db/models.py
```

### 4. Upload documents to Pinecone
Place `.txt` files in `knowledge_base/documents/` then run:
```bash
python agent/kb_chain.py
```

---

## Running the Agent

### Text mode (no microphone needed — best for testing)
```bash
python main.py --text
```

### Voice mode (microphone)
```bash
pip install pyaudio
python main.py
```

### Process an audio file
```bash
python main.py --file path/to/audio.wav
```

### REST API
```bash
python main.py --api
# → http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint         | Description                    |
|--------|------------------|--------------------------------|
| POST   | `/call`          | Process a customer message     |
| GET    | `/calls`         | List recent calls              |
| GET    | `/calls/{id}`    | Get full call record           |
| GET    | `/health`        | Liveness check                 |

### Example call
```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -d '{"customer_input": "My internet has been down for 2 days", "customer_name": "Ahmed"}'
```

---

## Architecture

```
Customer speaks
    ↓ STT (Groq Whisper)
Customer text
    ↓ Router  → intent + issue_category
    ↓ KB      → Pinecone similarity search → Groq LLM answer
    ↓ Brain   → natural reply generation
Agent reply text
    ↓ TTS (gTTS)
Spoken response
    ↓ DB      → CallReport saved (PostgreSQL)
    ↓ Monitor → recurring-issue check → email/Slack alert
```