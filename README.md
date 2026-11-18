<div align="center">

# 🎙️ OTA Support — Voice AI Support Agent

**CGI-ENSA Hackathon 2026**

> Voice agent that automates real-time technical troubleshooting for telecom support.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)

</div>

---

## 🚀 Overview

**OTA Support** is an AI-powered voice agent built for telecom customer support. It listens to customer calls in real time, understands the issue, searches a knowledge base, and responds with an accurate, human-like answer — all in seconds.

Built for the **CGI-ENSA Hackathon 2026**, this system demonstrates how conversational AI can automate first-level technical support for telecom operators.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Speech-to-Text** | Real-time transcription using **Groq Whisper** |
| 🧠 **RAG Pipeline** | Vector search with **Gemini Embeddings** + **Pinecone** |
| 💬 **LLM Reasoning** | Intelligent responses powered by **Groq LLM** |
| 🔌 **REST API** | Production-ready **FastAPI** backend |
| 🗄️ **Persistence** | Call history and reports stored in **PostgreSQL** |
| 📊 **Analytics** | Recurring issue detection & alert system |
| 🔊 **Text-to-Speech** | Spoken responses via gTTS |

---

## 🏗️ Architecture

```
Customer speaks
    ↓  STT — Groq Whisper
Customer text
    ↓  Router   → intent classification + issue category
    ↓  KB Chain → Pinecone similarity search → Groq LLM answer
    ↓  Brain    → natural, context-aware reply
Agent reply text
    ↓  TTS — gTTS
Spoken response
    ↓  DB      → CallReport saved to PostgreSQL
    ↓  Monitor → recurring-issue detection → alert
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Speech Recognition** | Groq Whisper |
| **LLM** | Groq (LLaMA / Mixtral) |
| **Embeddings** | Google Gemini Embeddings |
| **Vector DB** | Pinecone |
| **Backend** | FastAPI (Python) |
| **Database** | PostgreSQL + SQLAlchemy |
| **TTS** | gTTS |
| **Prompt Engineering** | Advanced multi-turn prompt design |

---

## 📁 Project Structure

```
OTA-SUPPORT/
└── voice-agent/
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
    │   ├── models.py         # SQLAlchemy models
    │   └── reports.py        # DB read/write helpers
    ├── knowledge_base/
    │   └── documents/        # .txt files ingested into Pinecone
    ├── ui/
    │   ├── index.html        # Web interface
    │   ├── app.js            # Frontend logic
    │   └── style.css         # Styling
    ├── stt.py                # Speech-to-Text
    ├── tts.py                # Text-to-Speech
    ├── main.py               # Entry point
    └── requirements.txt
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/zouinealifst-create/OTA-Support.git
cd OTA-Support
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r OTA-SUPPORT/voice-agent/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in `OTA-SUPPORT/voice-agent/`:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_index_name
DATABASE_URL=postgresql://user:password@localhost/ota_support_db
```

### 5. Initialize the database

```bash
psql -U postgres -c "CREATE DATABASE ota_support_db;"
python OTA-SUPPORT/voice-agent/db/models.py
```

### 6. Upload knowledge base to Pinecone

Place `.txt` files in `knowledge_base/documents/` then run:

```bash
python OTA-SUPPORT/voice-agent/agent/kb_chain.py
```

---

## ▶️ Running the Agent

```bash
# Text mode (no microphone — best for testing)
python OTA-SUPPORT/voice-agent/main.py --text

# Voice mode (microphone required)
python OTA-SUPPORT/voice-agent/main.py

# Process an audio file
python OTA-SUPPORT/voice-agent/main.py --file path/to/audio.wav

# REST API mode
python OTA-SUPPORT/voice-agent/main.py --api
# → Docs available at: http://localhost:8000/docs
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/call` | Process a customer message |
| `GET` | `/calls` | List recent calls |
| `GET` | `/calls/{id}` | Get full call record |
| `GET` | `/health` | Liveness check |

### Example

```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -d '{"customer_input": "My internet has been down for 2 days", "customer_name": "Ahmed"}'
```

---

## 👥 Team

Built with ❤️ for the **CGI-ENSA Hackathon 2026**

| Name | GitHub |
|------|--------|
| **Tarchi Oussama** | — |
| **Ali Zouine** | [@zouinealifst-create](https://github.com/zouinealifst-create) |
| **Taha Rajel** | — |

---

<div align="center">
<sub>OTA Support · CGI-ENSA Hackathon 2026 · Voice AI for Telecom</sub>
</div>
