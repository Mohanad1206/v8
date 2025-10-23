import time, random, requests, re, os
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from ..models import Product
from ..utils import parse_price_any, make_id

class HttpClient:
    def __init__(self, timeout: int = 25, delay_ms: int = 900, user_agent: Optional[str] = None):
        self.session = requests.Session()
        self.timeout = timeout
        self.delay_ms = delay_ms
        self.user_agent = user_agent or os.getenv("SCRAPER_USER_AGENT") or "Mozilla/5.0 (compatible; EdithScraper/2.0)"

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
        price = parse_price_any(txt)
        if price is not None:
            return price
    return None

class BaseProvider:
    def __init__(self, base_url: str, client: HttpClient):
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.source = urlparse(self.base_url).netloc

    def discover_product_urls(self, limit: int = 0) -> List[str]:
        raise NotImplementedError

    def parse_product(self, url: str) -> Optional[Product]:
        raise NotImplementedError

    def search(self, keywords: List[str], limit_pages: int = 0) -> List[Product]:
        raise NotImplementedError
