from .base import HttpClient, soup_from, og_content, guess_price
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import re

PROD_HINTS = ["product", "products", "item", "gaming", "mouse", "keyboard", "headset", "pad", "controller", "ps5", "xbox", "rgb"]

class HeuristicCatalogProvider:
    def __init__(self, base_url: str, client: HttpClient):
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.source = urlparse(self.base_url).netloc

    def discover_links(self, limit: int = 0) -> List[str]:
        urls: List[str] = []
        try:
            r = self.client.get(self.base_url)
            soup = soup_from(r)
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                full = urljoin(self.base_url, href)
                low = full.lower()
                if any(h in low for h in PROD_HINTS):
                    urls.append(full)
        except Exception:
            return []
        seen=set(); dedup=[]
        for u in urls:
            if u in seen: continue
            seen.add(u); dedup.append(u)
        return dedup if limit == 0 else dedup[:limit]

    def parse_product(self, url: str) -> Dict:
        r = self.client.get(url)
        soup = soup_from(r)
        title = og_content(soup, "og:title") or (soup.title.string if soup.title else "")
        price = guess_price(soup)
        img = og_content(soup, "og:image") or ""
        brand = og_content(soup, "product:brand")
        return {
            "name": title.strip(),
            "price_egp": float(price) if price is not None else None,
            "currency": "EGP",
            "url": url,
            "image_url": img,
            "brand": brand,
            "category": None,
            "source": self.source,
        }

    def search(self, keywords: List[str], limit_pages: int = 0) -> List[Dict]:
        out = []
        urls = self.discover_links(limit=limit_pages)
        for u in urls:
            try:
                item = self.parse_product(u)
                if not item["name"] or item["price_egp"] is None: continue
                if keywords:
                    low = item["name"].lower()
                    if not any(k.lower() in low for k in keywords): continue
                out.append(item)
            except Exception:
                continue
        return out
