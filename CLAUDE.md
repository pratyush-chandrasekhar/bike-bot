# Bike Troubleshooting Bot — Full Build Specification

## What to Build
A web app where users select a pre-loaded bike manual (PDF), then ask troubleshooting
questions using text, voice, or an image. The bot answers ONLY from that manual, in
whatever language the user writes in. Supports voice input (microphone) and voice output
(text-to-speech) using the browser's built-in Web Speech API — no extra packages needed.

## Existing Files — Do Not Touch
- `.env` — contains ANTHROPIC_API_KEY
- `manuals/` — folder with bike PDF files
- `venv/` — Python virtual environment
- `.gitignore`

## Files to Create
1. `main.py`
2. `index.html`
3. `requirements.txt`

---

## BACKEND — main.py

### Imports and initialization
```python
import os, fitz, chromadb, anthropic
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

db = chromadb.PersistentClient(path="./chroma_db")
claude = anthropic.Anthropic()
MANUALS = Path("./manuals")
```

### PDF ingestion
```python
def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size) if text[i:i+size].strip()]

def index_manual(path: Path):
    name = path.stem
    try:
        col = db.get_collection(name)
        if col.count() > 0:
            print(f"Already indexed: {name}"); return
    except:
        pass
    text = "".join(p.get_text() for p in fitz.open(str(path)))
    chunks = chunk_text(text)
    col = db.get_or_create_collection(name)
    col.add(documents=chunks, ids=[f"c{i}" for i in range(len(chunks))])
    print(f"Indexed {len(chunks)} chunks from {name}")

def index_all():
    for pdf in MANUALS.glob("*.pdf"):
        index_manual(pdf)
```

### FastAPI app with startup lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    index_all()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

### Endpoints

GET /bikes — scans manuals/ and returns available bikes
```python
@app.get("/bikes")
def get_bikes():
    return [
        {"id": p.stem, "name": p.stem.replace("_", " ").replace("-", " ").title()}
        for p in MANUALS.glob("*.pdf")
    ]
```

POST /chat — retrieves context from ChromaDB, calls Claude
```python
class ChatReq(BaseModel):
    bike_id: str
    query: str
    image: Optional[str] = None  # base64-encoded JPEG

@app.post("/chat")
def chat(req: ChatReq):
    col = db.get_collection(req.bike_id)
    docs = col.query(query_texts=[req.query], n_results=4)["documents"][0]
    context = "\n---\n".join(docs)

    system = (
        "You are a bike troubleshooting assistant. "
        "STRICT RULES:\n"
        "1. Answer ONLY using the manual excerpts provided below. Never use external knowledge.\n"
        "2. If the answer is not in the excerpts, say exactly: "
        "'I could not find this information in the manual.'\n"
        "3. Detect the language the user is writing in and respond in that exact same language.\n"
        "4. Keep answers practical and concise.\n\n"
        f"Manual excerpts:\n{context}"
    )

    content = req.query if not req.image else [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": req.image}},
        {"type": "text", "text": req.query}
    ]

    resp = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": content}]
    )
    return {"answer": resp.content[0].text}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
```

---

## FRONTEND — index.html

One file. All CSS and JS must be inline. No external libraries.

### HTML structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bike Troubleshooter</title>
  <style>/* all CSS here */</style>
</head>
<body>
  <div id="app">
    <header>
      <span id="title">🏍️ Bike Troubleshooter</span>
      <select id="bikeSelect"><option value="">Select your bike...</option></select>
      <button id="muteBtn" title="Toggle voice">🔊</button>
    </header>

    <main id="chat"></main>

    <footer>
      <div id="imgPreviewArea">
        <img id="imgPreview" alt="attached image">
        <button id="clearImgBtn">✕</button>
      </div>
      <div id="inputRow">
        <button id="micBtn" title="Hold to speak">🎤</button>
        <input id="msgInput" type="text" placeholder="Ask about your bike..." autocomplete="off">
        <label for="imgInput" id="imgBtn" title="Attach image">📎</label>
        <input id="imgInput" type="file" accept="image/*">
        <button id="sendBtn">Send</button>
      </div>
    </footer>
  </div>
  <script>/* all JS here */</script>
</body>
</html>
```

### CSS (write inside <style>)
Requirements:
- CSS custom properties: --primary: #2563eb, --bg: #f9fafb, --surface: #ffffff, --text: #111827, --muted: #6b7280, --radius: 16px
- body: margin 0, font-family system-ui sans-serif, background var(--bg), height 100vh, display flex, flex-direction column
- #app: max-width 720px, margin 0 auto, display flex, flex-direction column, height 100vh, width 100%
- header: display flex, align-items center, gap 10px, padding 12px 16px, background var(--surface), border-bottom 1px solid #e5e7eb, flex-shrink 0
- #title: font-weight 600, font-size 16px
- #bikeSelect: flex 1, max-width 240px, padding 6px 10px, border-radius 8px, border 1px solid #d1d5db, font-size 14px
- #muteBtn: background none, border none, font-size 20px, cursor pointer, padding 4px
- main#chat: flex 1, overflow-y auto, padding 16px, display flex, flex-direction column, gap 10px
- .msg: max-width 75%, padding 10px 14px, border-radius var(--radius), font-size 14px, line-height 1.6, word-break break-word
- .user: align-self flex-end, background var(--primary), color white, border-radius var(--radius) var(--radius) 4px var(--radius)
- .bot: align-self flex-start, background white, border 1px solid #e5e7eb, border-radius var(--radius) var(--radius) var(--radius) 4px
- .msg-row: display flex, align-items flex-end, gap 6px — wraps bot messages with a replay button
- .replay-btn: background none, border none, cursor pointer, font-size 14px, opacity 0.5, padding 2px
- .replay-btn:hover: opacity 1
- .typing: display flex, gap 4px, padding 12px 16px — shows animated dots
- .dot: width 8px, height 8px, border-radius 50%, background #9ca3af, animation bounce 1.2s infinite
- .dot:nth-child(2): animation-delay 0.2s
- .dot:nth-child(3): animation-delay 0.4s
- @keyframes bounce: 0%,80%,100% transform translateY(0); 40% transform translateY(-8px)
- footer: padding 12px 16px, background var(--surface), border-top 1px solid #e5e7eb, flex-shrink 0
- #imgPreviewArea: display none, align-items center, gap 8px, margin-bottom 8px
- #imgPreview: height 56px, border-radius 8px, object-fit cover
- #clearImgBtn: background none, border none, cursor pointer, font-size 18px, color var(--muted)
- #inputRow: display flex, gap 8px, align-items center
- #msgInput: flex 1, padding 10px 14px, border-radius 24px, border 1px solid #d1d5db, font-size 14px, outline none
- #msgInput:focus: border-color var(--primary)
- #sendBtn: padding 10px 18px, background var(--primary), color white, border none, border-radius 24px, cursor pointer, font-size 14px, font-weight 500
- #micBtn: background none, border 1px solid #d1d5db, border-radius 50%, width 40px, height 40px, cursor pointer, font-size 18px, flex-shrink 0
- #micBtn.recording: background #ef4444, border-color #ef4444, animation pulse 1s ease-in-out infinite
- @keyframes pulse: 0%,100% opacity 1; 50% opacity 0.6
- #imgBtn: cursor pointer, font-size 20px, padding 4px, user-select none
- #imgInput: display none

### JavaScript (write inside <script>)

**State variables:**
```javascript
let selectedBike = null;
let imageBase64 = null;
let isMuted = false;
let isRecording = false;
```

**DOM refs:** get all elements by id

**appendMessage(role, text):**
- Create div.msg with class user or bot
- For 'user': set textContent to text, append to chat
- For 'bot': create a .msg-row div containing the .msg div and a .replay-btn button (🔊)
  - replay-btn onclick calls speak(text)
  - append msg-row to chat
- Scroll chat to bottom

**showTyping() / hideTyping():**
- Show: create div#typing with 3 div.dot children, append to chat, scroll to bottom
- Hide: remove element with id 'typing'

**loadBikes():**
- fetch('/bikes'), populate bikeSelect options
- If only one bike returned, auto-select it and set selectedBike

**sendMessage():**
- Get query from msgInput, trim. Return if empty or !selectedBike
- appendMessage('user', query + (imageBase64 ? ' 📷' : ''))
- Clear msgInput
- showTyping()
- POST /chat with JSON {bike_id: selectedBike, query, image: imageBase64}
- On success: hideTyping(), appendMessage('bot', data.answer), speak(data.answer), clearImage()
- On error: hideTyping(), appendMessage('bot', 'Error: Could not reach server.')

**speak(text):**
- If isMuted or !window.speechSynthesis: return
- window.speechSynthesis.cancel()
- Create new SpeechSynthesisUtterance(text)
- Set utterance.lang = navigator.language
- window.speechSynthesis.speak(utterance)

**toggleMute():**
- Toggle isMuted
- Update muteBtn text: isMuted ? '🔇' : '🔊'
- If muting: window.speechSynthesis.cancel()

**Voice input setup:**
```javascript
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SR) {
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = navigator.language;

    recognition.onresult = e => {
        msgInput.value = e.results[0][0].transcript;
        stopRec();
        sendMessage();
    };
    recognition.onerror = e => { stopRec(); appendMessage('bot', 'Voice error: ' + e.error); };
    recognition.onend = () => stopRec();
}

function toggleRec() {
    if (!SR) { appendMessage('bot', 'Voice input requires Chrome. Try typing instead.'); return; }
    isRecording ? stopRec() : startRec();
}
function startRec() {
    isRecording = true;
    micBtn.classList.add('recording');
    recognition.start();
}
function stopRec() {
    isRecording = false;
    micBtn.classList.remove('recording');
    try { recognition.stop(); } catch(e) {}
}
```

**Image input:**
```javascript
imgInput.onchange = e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
        imageBase64 = ev.target.result.split(',')[1];
        imgPreview.src = ev.target.result;
        imgPreviewArea.style.display = 'flex';
    };
    reader.readAsDataURL(file);
};

function clearImage() {
    imageBase64 = null;
    imgInput.value = '';
    imgPreviewArea.style.display = 'none';
}
```

**Event listeners:**
```javascript
sendBtn.onclick = sendMessage;
msgInput.onkeydown = e => { if (e.key === 'Enter') sendMessage(); };
micBtn.onclick = toggleRec;
muteBtn.onclick = toggleMute;
clearImgBtn.onclick = clearImage;
bikeSelect.onchange = () => {
    selectedBike = bikeSelect.value;
    if (selectedBike) {
        const name = bikeSelect.options[bikeSelect.selectedIndex].text;
        appendMessage('bot', `Ready! Ask me anything about the ${name}. You can type, speak, or send an image.`);
    }
};

loadBikes();
```

---

## requirements.txt
```
fastapi
uvicorn[standard]
pymupdf
chromadb
anthropic
python-dotenv
python-multipart
```

---

## After Creating All Files

Run: `uvicorn main:app --reload`
Open: `http://localhost:8000`

### Test checklist
- [ ] Bike dropdown populates with PDF names from manuals/
- [ ] Selecting a bike shows a welcome message
- [ ] Typing a question returns an answer from the manual
- [ ] Asking something NOT in the manual returns "I could not find this in the manual."
- [ ] Microphone button (Chrome only): click, speak a question, it auto-sends
- [ ] Bot answers are read aloud automatically
- [ ] Mute button silences voice output
- [ ] 🔊 replay button on each bot message re-reads it
- [ ] Attaching an image (📎) and asking about it works
- [ ] Typing in Hindi / Tamil / Spanish / French returns a response in that language
