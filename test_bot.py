import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
BIKE = "royal_enfield_bullet_650"
results = []

def has_script(text, lo, hi):
    return any(lo <= ord(ch) <= hi for ch in text)

def is_tamil(text):   return has_script(text, 0x0B80, 0x0BFF)
def is_arabic(text):  return has_script(text, 0x0600, 0x06FF)
def is_hindi(text):   return has_script(text, 0x0900, 0x097F)
def is_latin(text):   return any(ch.isascii() and ch.isalpha() for ch in text)

def check(n, label, r, passed, reason=""):
    status = "PASS" if passed else "FAIL"
    print(f"\n{'='*60}")
    print(f"{n}. {label}")
    print(f"{'='*60}")
    print(f"Status: {r.status_code}")
    body = r.json()
    ans = body.get("answer", r.text) if isinstance(body, dict) else str(body)
    print(f"Answer: {ans}")
    print(f"=> {status}" + (f": {reason}" if reason else ""))
    results.append((n, label, passed, reason))

# 1. GET /bikes
r = requests.get(f"{BASE}/bikes")
bikes = r.json()
ok = r.status_code == 200 and len(bikes) >= 1
check(1, "GET /bikes", r, ok, "" if ok else "No bikes returned")

# 2. Tyre pressure (English)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "what is the tyre pressure"})
ans = r.json().get("answer", "")
lang_ok = is_latin(ans) and not is_tamil(ans) and not is_arabic(ans) and not is_hindi(ans)
content_ok = any(x in ans for x in ["32", "36", "42", "psi"])
ok = r.status_code == 200 and lang_ok and content_ok
check(2, "POST /chat - tyre pressure (English)", r,
      ok, "" if ok else f"lang_ok={lang_ok} content_ok={content_ok}")

# 3. Price (not in manual)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "what is the price of the bike"})
ans = r.json().get("answer", "")
refused = any(w in ans.lower() for w in ["not find", "not found", "not in the manual",
                                          "cannot find", "does not", "no information",
                                          "not covered", "not specifically", "could not"])
ok = r.status_code == 200 and refused
check(3, "POST /chat - price (NOT in manual)", r,
      ok, "" if ok else "Should say info not in manual")

# 4. Tyre pressure (Hindi)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "टायर प्रेशर क्या होना चाहिए"})
ans = r.json().get("answer", "")
lang_ok = is_hindi(ans)
content_ok = any(x in ans for x in ["32", "36", "42", "psi"])
ok = r.status_code == 200 and lang_ok and content_ok
check(4, "POST /chat - tyre pressure (Hindi)", r,
      ok, "" if ok else f"lang_ok={lang_ok} content_ok={content_ok}")

# 5. Oil quantity (Tamil)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "என் பைக்கில் எண்ணெய் எவ்வளவு"})
ans = r.json().get("answer", "")
lang_ok = is_tamil(ans)
content_ok = any(x in ans for x in ["litre", "liter", "ml", "L", "1.", "2.", "3.", "0."]) or \
             any(x in ans.lower() for x in ["could not find", "not find", "not in"])
ok = r.status_code == 200 and lang_ok
check(5, "POST /chat - oil quantity (Tamil)", r,
      ok, "" if ok else f"lang_ok={lang_ok} (expected Tamil script in response)")

# 6. Tyre pressure (Arabic)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "ما هو ضغط الإطارات"})
ans = r.json().get("answer", "")
lang_ok = is_arabic(ans)
content_ok = any(x in ans for x in ["32", "36", "42", "psi"])
ok = r.status_code == 200 and lang_ok and content_ok
check(6, "POST /chat - tyre pressure (Arabic)", r,
      ok, "" if ok else f"lang_ok={lang_ok} content_ok={content_ok}")

# 7. Tyre pressure (French)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "quelle est la pression des pneus"})
ans = r.json().get("answer", "")
french_words = ["pression", "pneu", "avant", "arrière", "arriere", "bar", "solo", "passager",
                "32", "36", "42", "psi"]
lang_ok = is_latin(ans) and not is_tamil(ans) and not is_arabic(ans) and not is_hindi(ans)
content_ok = any(w in ans.lower() for w in french_words)
ok = r.status_code == 200 and lang_ok and content_ok
check(7, "POST /chat - tyre pressure (French)", r,
      ok, "" if ok else f"lang_ok={lang_ok} content_ok={content_ok}")

# 8. Strange noise (English, vague)
r = requests.post(f"{BASE}/chat", json={"bike_id": BIKE, "query": "my bike is making a strange noise"})
ans = r.json().get("answer", "")
lang_ok = is_latin(ans) and not is_tamil(ans) and not is_arabic(ans) and not is_hindi(ans)
has_content = len(ans.strip()) > 20
ok = r.status_code == 200 and lang_ok and has_content
check(8, "POST /chat - strange noise (English, vague)", r,
      ok, "" if ok else f"lang_ok={lang_ok} has_content={has_content}")

# Summary
print(f"\n{'='*60}")
passed = sum(1 for _, _, p, _ in results if p)
print(f"SUMMARY: {passed}/{len(results)} passed")
if any(not p for _, _, p, _ in results):
    print("Failed:")
    for n, label, p, reason in results:
        if not p:
            print(f"  [{n}] {label}: {reason}")
