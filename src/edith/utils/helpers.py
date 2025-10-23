import re, hashlib
from typing import Optional, List
from urllib.parse import urlparse

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

def make_id(source: str, name: str, price: Optional[float], url: str) -> str:
    """Stable ID not tied to price (so price updates don't change ID).
    Uses normalized name + source + url.
    """
    base = f"{source}|{norm_name(name)}|{url}"
    return hashlib.md5(base.encode()).hexdigest()[:12]

def is_gaming_accessory(name: str, exclude_keywords: List[str]) -> bool:
    """Check if product is a gaming accessory, excluding specified keywords."""
    name_lower = name.lower()
    # Include gaming-related terms
    include_terms = ["gaming", "keyboard", "mouse", "headset", "controller", "joystick", "pad", "steering", "wheel"]
    if not any(term in name_lower for term in include_terms):
        return False
    # Exclude specified keywords
    if any(excl in name_lower for excl in exclude_keywords):
        return False
    return True
