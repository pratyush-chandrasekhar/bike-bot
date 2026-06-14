"""
Comprehensive live test for Bike Troubleshooter Bot
Target: https://bike-bot-production-83fc.up.railway.app/
"""

import requests
import base64
import json
import io
import wave
import struct
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://bike-bot-production-83fc.up.railway.app"
TIMEOUT  = 60  # seconds — Railway cold starts can be slow

passed = 0
failed = 0
bugs   = []
output_lines = []

BIKE_ID = "royal_enfield_bullet_650"

# ── Minimal 1x1 white JPEG ─────────────────────────────────────────────────
MINIMAL_JPEG = bytes([
    0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,
    0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,
    0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,
    0x0C,0x0B,0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,
    0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,
    0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,
    0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,0x00,0x01,
    0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,0x01,0x05,0x01,0x01,
    0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,
    0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0xFF,0xC4,0x00,0xB5,0x10,
    0x00,0x02,0x01,0x03,0x03,0x02,0x04,0x03,0x05,0x05,0x04,0x04,0x00,0x00,
    0x01,0x7D,0x01,0x02,0x03,0x00,0x04,0x11,0x05,0x12,0x21,0x31,0x41,0x06,
    0x13,0x51,0x61,0x07,0x22,0x71,0x14,0x32,0x81,0x91,0xA1,0x08,0x23,0x42,
    0xB1,0xC1,0x15,0x52,0xD1,0xF0,0x24,0x33,0x62,0x72,0x82,0x09,0x0A,0x16,
    0x17,0x18,0x19,0x1A,0x25,0x26,0x27,0x28,0x29,0x2A,0x34,0x35,0x36,0x37,
    0x38,0x39,0x3A,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x53,0x54,0x55,
    0x56,0x57,0x58,0x59,0x5A,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,0x73,
    0x74,0x75,0x76,0x77,0x78,0x79,0x7A,0x83,0x84,0x85,0x86,0x87,0x88,0x89,
    0x8A,0x92,0x93,0x94,0x95,0x96,0x97,0x98,0x99,0x9A,0xA2,0xA3,0xA4,0xA5,
    0xA6,0xA7,0xA8,0xA9,0xAA,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,0xB9,0xBA,
    0xC2,0xC3,0xC4,0xC5,0xC6,0xC7,0xC8,0xC9,0xCA,0xD2,0xD3,0xD4,0xD5,0xD6,
    0xD7,0xD8,0xD9,0xDA,0xE1,0xE2,0xE3,0xE4,0xE5,0xE6,0xE7,0xE8,0xE9,0xEA,
    0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0xF7,0xF8,0xF9,0xFA,0xFF,0xDA,0x00,0x08,
    0x01,0x01,0x00,0x00,0x3F,0x00,0xFB,0xD7,0xFF,0xD9,
])
SAMPLE_IMAGE_B64 = base64.b64encode(MINIMAL_JPEG).decode()

# ── Minimal silent WAV for audio test ─────────────────────────────────────
def make_wav_bytes(duration_ms=200, sample_rate=16000):
    n = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    buf.seek(0)
    return buf.read()

SAMPLE_WAV = make_wav_bytes()

# ── Helpers ────────────────────────────────────────────────────────────────
SEP = "=" * 65

def emit(line):
    print(line)
    output_lines.append(line)

def record(name, req_summary, resp_summary, ok, reason=""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    icon   = "✅" if ok else "❌"
    emit(SEP)
    emit(f"{icon}  {name}")
    emit(f"   REQUEST : {req_summary}")
    emit(f"   RESPONSE: {resp_summary}")
    emit(f"   STATUS  : {status}" + (f" — {reason}" if reason else ""))
    if ok:
        passed += 1
    else:
        failed += 1
        bugs.append(f"[{name}] {reason}")

# ── Tests ──────────────────────────────────────────────────────────────────

emit(SEP)
emit(f"  Bike Bot Live Test  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
emit(f"  Target: {BASE_URL}")
emit(SEP)

# 1. GET /bikes
try:
    r = requests.get(f"{BASE_URL}/bikes", timeout=TIMEOUT)
    raw = r.json()
    emit(f"   [DEBUG] /bikes raw response: {repr(raw)[:200]}")
    bikes = raw if isinstance(raw, list) else []
    if bikes and isinstance(bikes[0], dict):
        ids = [b.get("id", "?") for b in bikes]
    else:
        ids = bikes
    ok = r.status_code == 200 and len(bikes) == 5
    reason = "" if ok else f"Expected 5 bike dicts, got {len(bikes)} items: {ids}"
    record("GET /bikes — 5 bikes returned",
           "GET /bikes",
           f"HTTP {r.status_code} | {len(bikes)} bikes: {ids}",
           ok, reason)
except Exception as e:
    record("GET /bikes — 5 bikes returned", "GET /bikes", f"Exception: {e}", False, str(e))

# 2. POST /chat — English, in manual
try:
    body = {"bike_id": BIKE_ID, "query": "what is the tyre pressure"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    ok = r.status_code == 200 and len(answer) > 20 and "could not find" not in answer.lower()
    reason = "" if ok else f"Answer too short or not found: {answer[:120]}"
    record("POST /chat — English (in manual)",
           json.dumps(body),
           f"HTTP {r.status_code} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — English (in manual)", str(body), f"Exception: {e}", False, str(e))

# 3. POST /chat — Question NOT in manual
try:
    body = {"bike_id": BIKE_ID, "query": "what is the price of the bike"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    ok = r.status_code == 200 and (
        "could not find" in answer.lower()
        or "not in the manual" in answer.lower()
        or "manual" in answer.lower()
    )
    reason = "" if ok else f"Expected 'not found' response, got: {answer[:120]}"
    record("POST /chat — Out-of-manual question",
           json.dumps(body),
           f"HTTP {r.status_code} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Out-of-manual question", str(body), f"Exception: {e}", False, str(e))

# 4. POST /chat — Hindi (Devanagari)
try:
    body = {"bike_id": BIKE_ID, "query": "टायर प्रेशर क्या होना चाहिए"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in answer)
    ok = r.status_code == 200 and len(answer) > 10 and has_devanagari
    reason = "" if ok else (
        f"Response not in Hindi script (Devanagari). Answer: {answer[:120]}"
    )
    record("POST /chat — Hindi Devanagari",
           json.dumps(body),
           f"HTTP {r.status_code} | Hindi script: {has_devanagari} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Hindi Devanagari", str(body), f"Exception: {e}", False, str(e))

# 5. POST /chat — Tamil
try:
    body = {"bike_id": BIKE_ID, "query": "டயர் அழுத்தம் என்ன"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    has_tamil = any(0x0B80 <= ord(c) <= 0x0BFF for c in answer)
    ok = r.status_code == 200 and len(answer) > 10 and has_tamil
    reason = "" if ok else f"Response not in Tamil script. Answer: {answer[:120]}"
    record("POST /chat — Tamil",
           json.dumps(body),
           f"HTTP {r.status_code} | Tamil script: {has_tamil} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Tamil", str(body), f"Exception: {e}", False, str(e))

# 6. POST /chat — Arabic
try:
    body = {"bike_id": BIKE_ID, "query": "ما هو ضغط الإطارات"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    has_arabic = any(0x0600 <= ord(c) <= 0x06FF for c in answer)
    ok = r.status_code == 200 and len(answer) > 10 and has_arabic
    reason = "" if ok else f"Response not in Arabic script. Answer: {answer[:120]}"
    record("POST /chat — Arabic",
           json.dumps(body),
           f"HTTP {r.status_code} | Arabic script: {has_arabic} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Arabic", str(body), f"Exception: {e}", False, str(e))

# 7. POST /chat — Vague question needing inference
try:
    body = {"bike_id": BIKE_ID, "query": "my bike is making strange noise what should I do"}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    ok = r.status_code == 200 and len(answer) > 30
    reason = "" if ok else f"Expected substantive answer, got: {answer[:120]}"
    record("POST /chat — Vague/inference question",
           json.dumps(body),
           f"HTTP {r.status_code} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Vague/inference question", str(body), f"Exception: {e}", False, str(e))

# 8. POST /chat — With image
try:
    body = {"bike_id": BIKE_ID, "query": "what does this show", "image": SAMPLE_IMAGE_B64}
    r = requests.post(f"{BASE_URL}/chat", json=body, timeout=TIMEOUT)
    data = r.json()
    answer = data.get("answer", "")
    ok = r.status_code == 200 and len(answer) > 10
    reason = "" if ok else f"Expected answer with image, got: {answer[:120]}"
    record("POST /chat — Image upload (1×1 JPEG)",
           f'{{"bike_id":"{BIKE_ID}","query":"what does this show","image":"<base64>"}}',
           f"HTTP {r.status_code} | {answer[:120]}...",
           ok, reason)
except Exception as e:
    record("POST /chat — Image upload (1×1 JPEG)",
           "POST /chat with image", f"Exception: {e}", False, str(e))

# 9. POST /transcribe — Silent WAV (sent as webm)
try:
    files = {"audio": ("recording.webm", io.BytesIO(SAMPLE_WAV), "audio/webm")}
    r = requests.post(f"{BASE_URL}/transcribe", files=files, timeout=TIMEOUT)
    ok = r.status_code == 200
    try:
        data = r.json()
        resp_summary = f"HTTP {r.status_code} | {data}"
        # Empty transcript is fine for silent audio; error key means failure
        if "error" in data:
            ok = False
            reason = f"Transcribe returned error: {data}"
        else:
            reason = "" if ok else f"HTTP {r.status_code}"
    except Exception:
        resp_summary = f"HTTP {r.status_code} | {r.text[:120]}"
        reason = f"Non-JSON response: {r.text[:120]}"
        ok = False
    record("POST /transcribe — Silent audio blob",
           "POST /transcribe (200ms silent WAV as audio/webm)",
           resp_summary, ok, reason)
except Exception as e:
    record("POST /transcribe — Silent audio blob",
           "POST /transcribe", f"Exception: {e}", False, str(e))

# 10. POST /speak — TTS
try:
    body = {"text": "hello this is a test"}
    r = requests.post(f"{BASE_URL}/speak", json=body, timeout=TIMEOUT)
    content_type = r.headers.get("content-type", "")
    ok = r.status_code == 200 and "audio/mpeg" in content_type and len(r.content) > 500
    reason = "" if ok else (
        f"Expected audio/mpeg with content, got {content_type}, {len(r.content)} bytes"
    )
    record("POST /speak — gTTS audio response",
           json.dumps(body),
           f"HTTP {r.status_code} | Content-Type: {content_type} | {len(r.content)} bytes",
           ok, reason)
except Exception as e:
    record("POST /speak — gTTS audio response",
           str(body), f"Exception: {e}", False, str(e))

# 11. GET /health
try:
    r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    if r.status_code == 200:
        try:
            data = r.json()
            ok = data.get("status") == "ok"
            reason = "" if ok else f"Expected {{status: ok}}, got {data}"
            resp_summary = f"HTTP {r.status_code} | {data}"
        except Exception:
            ok = False
            reason = f"Non-JSON response: {r.text[:80]}"
            resp_summary = f"HTTP {r.status_code} | {r.text[:80]}"
    else:
        ok = False
        reason = f"HTTP {r.status_code} — endpoint not implemented"
        resp_summary = f"HTTP {r.status_code}"
    record("GET /health — health check endpoint",
           "GET /health",
           resp_summary, ok, reason)
except Exception as e:
    record("GET /health — health check endpoint",
           "GET /health", f"Exception: {e}", False, str(e))

# ── Summary ────────────────────────────────────────────────────────────────
emit(SEP)
emit(f"  RESULTS: {passed} passed, {failed} failed  (total {passed + failed})")
emit(SEP)

if bugs:
    emit("\n  BUGS FOUND:")
    for i, bug in enumerate(bugs, 1):
        emit(f"  {i}. {bug}")
    emit("")
    emit("  SUGGESTED FIXES:")
    for bug in bugs:
        name = bug.split("]")[0].lstrip("[")
        if "health" in name.lower():
            emit(f"  → Add GET /health endpoint to main.py returning {{\"status\": \"ok\"}}")
        elif "Tamil" in name:
            emit(f"  → Tamil: verify detect_language() range and system prompt enforcement")
        elif "Arabic" in name:
            emit(f"  → Arabic: same as Tamil — check script detection ranges")
        elif "Hindi" in name:
            emit(f"  → Hindi: check Devanagari range 0x0900–0x097F in detect_language()")
        elif "out-of-manual" in name.lower() or "Out-of-manual" in name:
            emit(f"  → Out-of-manual: tighten system prompt rule #4 to refuse more firmly")
        elif "image" in name.lower():
            emit(f"  → Image: check vision model fallback and base64 decoding in /chat")
        elif "transcribe" in name.lower():
            emit(f"  → Transcribe: Groq Whisper may reject non-WebM audio; check error handling")
        elif "speak" in name.lower():
            emit(f"  → Speak: check gTTS install on Railway and /speak endpoint in main.py")
        elif "5 bikes" in name.lower():
            emit(f"  → Bikes: verify all 5 PDFs are present and indexed in manuals/")
else:
    emit("  No bugs found — all endpoints passed!")

emit(SEP)

# ── Write to file ──────────────────────────────────────────────────────────
with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print(f"\nResults saved to test_results.txt")
