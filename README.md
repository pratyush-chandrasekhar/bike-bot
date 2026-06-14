# 🏍️ Bike Troubleshooter Bot

> An AI-powered bike troubleshooting chatbot that answers questions strictly from official bike owner manuals using RAG (Retrieval Augmented Generation).

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Railway-6366f1?style=for-the-badge&logo=railway)](https://bike-bot-production-83fc.up.railway.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

---

## ✨ Features

- **Manual-grounded answers** — The bot answers *only* from the official owner's manual. It never makes things up or uses external knowledge.
- **Voice input** — Speak your question in any language using Groq Whisper (state-of-the-art multilingual speech recognition).
- **Voice output** — Responses are read aloud in any language using gTTS, with a pause/resume mute button.
- **Image upload** — Photograph a part, warning light, or damage and ask about it directly.
- **Fully multilingual** — Type or speak in English, Hindi, Hinglish, Tamil, French, Spanish, or any language — the bot responds in the same language and script.
- **5 Royal Enfield manuals preloaded** — Ready to use out of the box.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Vector DB | ChromaDB (persistent RAG store) |
| LLM | Groq LLaMA 3.3 70B |
| Vision | Groq LLaMA 4 Scout (image analysis) |
| Speech-to-Text | Groq Whisper Large v3 Turbo |
| Text-to-Speech | gTTS (Google Text-to-Speech) |
| PDF Parsing | PyMuPDF |
| Frontend | Vanilla HTML/CSS/JS (single file, dark theme) |
| Deployment | Railway |

---

## 📖 Manuals Included

| Bike | Manual |
|---|---|
| Royal Enfield Bullet 650 | ✅ |
| Royal Enfield Classic 650 | ✅ |
| Royal Enfield Meteor 350 | ✅ |
| Royal Enfield Interceptor 650 | ✅ |
| Royal Enfield Goan Classic 350 | ✅ |

---

## 🚀 Run Locally

**Prerequisites:** Python 3.11+, Chrome (for voice input)

```bash
# 1. Clone the repository
git clone https://github.com/pratyush-chandrasekhar/bike-bot.git
cd bike-bot

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
echo GROQ_API_KEY=your_key_here > .env

# 5. Add bike PDF manuals
# Drop your PDF files into the manuals/ folder

# 6. Start the server
uvicorn main:app --reload

# 7. Open in browser
# http://localhost:8000
```

> **Note:** ChromaDB indexes the manuals automatically on first startup. Subsequent starts are instant.

---

## 🧠 How It Works

1. **Indexing** — On startup, each PDF in `manuals/` is parsed, chunked into 500-character segments, and embedded into a ChromaDB vector store.
2. **Retrieval** — When a user asks a question, the top 4 most semantically relevant chunks are retrieved. For non-Latin scripts, the query is first translated to English for better retrieval, then the original is also queried and results are merged.
3. **Generation** — The retrieved chunks are passed as context to Groq LLaMA 3.3 70B with a strict system prompt: answer only from the manual, respond in the user's exact language and script.
4. **Voice** — Audio input goes to Groq Whisper for transcription. The text response is sent to gTTS for playback.

---

## 👨‍💻 Built By

**Pratyush Chandrasekhar** — 3rd year BTech IT student

---

## 🤖 Built With Claude Code

This project was built using [Claude Code](https://claude.ai/code) (Anthropic's AI coding assistant) as part of learning how to build AI-powered applications. The architecture, debugging, deployment, and all technical decisions were made collaboratively through the development process.
