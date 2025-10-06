import re, hashlib
from typing import Optional

PRICE_RE = re.compile(r'(?<!\d)(\d{2,6}(?:[.,]\d{2})?)(?!\d)')

def parse_price_any(text: str) -> Optional[float]:
    if not text: return None
    t = text.replace('\u00a0',' ').replace(',', '')
    m = PRICE_RE.search(t)
    if not m: return None
    try: return float(m.group(1))
    except: return None

def norm_name(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9+ ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def make_id(source: str, name: str, price: float, url: str) -> str:
    return hashlib.md5(f"{source}|{name}|{price}|{url}".encode()).hexdigest()[:12]
