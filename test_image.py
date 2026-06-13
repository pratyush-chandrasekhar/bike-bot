import requests, base64, sys, io
sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image
    img = Image.new('RGB', (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    print('Image source: PIL')
except ImportError:
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=10, height=10)
    pix = page.get_pixmap()
    b64 = base64.b64encode(pix.tobytes("jpeg")).decode()
    print('Image source: PyMuPDF')

print(f'Base64 length: {len(b64)} chars')

r = requests.post('http://localhost:8000/chat', json={
    'bike_id': 'royal_enfield_bullet_650',
    'query': 'what does this image show',
    'image': b64
}, timeout=30)

print(f'Status: {r.status_code}')
try:
    print(f'Response: {r.json()}')
except Exception:
    print(f'Raw: {r.text}')
