import io, os, re, fitz, chromadb, traceback
from groq import Groq
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

db = chromadb.PersistentClient(path="./chroma_db")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MANUALS = Path("./manuals")


def sanitize_name(stem: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', stem)
    return name.strip('_-')


def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size) if text[i:i+size].strip()]


def index_manual(path: Path):
    name = sanitize_name(path.stem)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    index_all()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/bikes")
def get_bikes():
    return [
        {"id": sanitize_name(p.stem), "name": p.stem.replace("_", " ").replace("-", " ").title()}
        for p in MANUALS.glob("*.pdf")
    ]


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    contents = await audio.read()
    transcription = groq_client.audio.transcriptions.create(
        file=("recording.webm", io.BytesIO(contents), "audio/webm"),
        model="whisper-large-v3-turbo",
        response_format="text"
    )
    return {"transcript": str(transcription)}


class ChatReq(BaseModel):
    bike_id: str
    query: str
    image: Optional[str] = None  # base64-encoded JPEG


def detect_language(text: str) -> str | None:
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F: return "Hindi"
        if 0x0B80 <= cp <= 0x0BFF: return "Tamil"
        if 0x0D00 <= cp <= 0x0D7F: return "Malayalam"
        if 0x0C00 <= cp <= 0x0C7F: return "Telugu"
        if 0x0A00 <= cp <= 0x0A7F: return "Punjabi"
        if 0x0980 <= cp <= 0x09FF: return "Bengali"
        if 0x0600 <= cp <= 0x06FF: return "Arabic"
    return None  # Latin-script (English, French, Spanish, etc.) — let the model detect


@app.post("/chat")
def chat(req: ChatReq):
  try:
    user_language = detect_language(req.query)

    # For non-Latin scripts the embedding model may not bridge well to Tamil/English manual
    # chunks, so translate the query to English for retrieval only.
    retrieval_query = req.query
    if user_language and user_language != "English":
        trans_resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Translate this query to English in 10 words or fewer. Output only the translation, nothing else: {req.query}"
            }],
            max_tokens=30
        )
        retrieval_query = trans_resp.choices[0].message.content.strip()

    col = db.get_collection(req.bike_id)
    if retrieval_query != req.query:
        # Merge results from translated + original queries, deduplicate by content
        docs_translated = col.query(query_texts=[retrieval_query], n_results=4)["documents"][0]
        docs_original = col.query(query_texts=[req.query], n_results=4)["documents"][0]
        seen, docs = set(), []
        for d in docs_translated + docs_original:
            key = d[:80]
            if key not in seen:
                seen.add(key)
                docs.append(d)
        docs = docs[:6]
    else:
        docs = col.query(query_texts=[req.query], n_results=4)["documents"][0]
    context = "\n---\n".join(docs)

    if user_language:
        lang_prefix = (
            f"The user's query is written in {user_language}. "
            f"YOU MUST RESPOND ENTIRELY IN {user_language}. "
            f"Do not use any other language, even if the manual excerpts are in a different language.\n\n"
        )
        lang_suffix = f"\nREMINDER: Your entire response must be in {user_language} only."
    else:
        lang_prefix = (
            "Detect the exact language AND script of the user's query and follow these rules strictly:\n"
            "- If the user writes in Hinglish (Hindi words typed in Roman/Latin script, "
            "e.g. 'bike ki problem kya hai' or 'engine start nahi ho raha'), "
            "respond ENTIRELY in Hinglish Roman script. "
            "Do NOT use Devanagari characters. Do NOT write Hindi words in Devanagari. "
            "Do NOT mix Devanagari and Latin in the same response.\n"
            "- If the user writes in English, French, Spanish, or any other Latin-script language, "
            "respond entirely in that language.\n"
            "- NEVER mix scripts in a single response. Match the exact script and style the user used.\n"
            "Ignore the language of the manual excerpts when deciding your response language.\n\n"
        )
        lang_suffix = "\nREMINDER: Match the exact script and style the user wrote in. Never mix scripts in one response."

    system = (
        f"You are a bike troubleshooting assistant. {lang_prefix}"
        "RULES:\n"
        "1. Answer using whatever relevant information exists in the manual excerpts below. Never use external knowledge.\n"
        "2. Always clearly state what the manual says, even if it doesn't perfectly match the user's exact question.\n"
        "3. If the user's specific scenario isn't fully covered, say what the manual does say, then add what the manual implies.\n"
        "4. Only say 'I could not find this information in the manual.' if there is genuinely zero relevant information in the excerpts.\n"
        "5. Keep answers practical and concise.\n\n"
        f"Manual excerpts:\n{context}"
        f"{lang_suffix}"
    )

    if req.image:
        try:
            resp = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{req.image}"}},
                        {"type": "text", "text": req.query}
                    ]}
                ]
            )
        except Exception as vision_err:
            traceback.print_exc()
            print(f"Vision model failed ({vision_err}), falling back to text-only")
            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": req.query}]
            )
    else:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": req.query}]
        )

    return {"answer": resp.choices[0].message.content}
  except Exception:
    traceback.print_exc()
    raise


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/speak")
async def speak_text(body: dict):
    text = body.get("text", "")
    try:
        from gtts import gTTS
        from langdetect import detect
        try:
            lang = detect(text)
        except:
            lang = "en"
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(audio_buffer, media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS error: {e}")
        return {"error": str(e)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
