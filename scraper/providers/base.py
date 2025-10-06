import time, random, requests, re
from typing import Optional
from bs4 import BeautifulSoup

class HttpClient:
    def __init__(self, timeout: int = 20, delay_ms: int = 700, user_agent: Optional[str] = None):
        self.session = requests.Session()
        self.timeout = timeout
        self.delay_ms = delay_ms
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; EdithScraper/2.0)"

    def get(self, url: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self.user_agent)
        headers.setdefault("Accept-Language", "en-EG,en;q=0.9,ar-EG;q=0.8")
        time.sleep((self.delay_ms + random.randint(0, 300)) / 1000.0)
        resp = self.session.get(url, headers=headers, timeout=self.timeout, **kwargs)
        resp.raise_for_status()
        return resp

def soup_from(resp) -> BeautifulSoup:
    return BeautifulSoup(resp.text, "lxml")

def og_content(soup: BeautifulSoup, prop: str):
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return tag["content"].strip() if tag and tag.get("content") else None

def guess_price(soup: BeautifulSoup):
    for prop in ["product:price:amount", "og:price:amount"]:
        c = og_content(soup, prop)
        if c:
            try: return float(c.replace(",", ""))
            except: pass
    cand = soup.select("[class*=price], [id*=price]")
    for el in cand[:10]:
        txt = el.get_text(" ", strip=True)
        m = re.search(r'(\d{2,6}(?:[.,]\d{2})?)', txt.replace(',', ''))
        if m:
            try: return float(m.group(1))
            except: pass
    return None
