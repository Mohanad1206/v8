from .base import HttpClient, soup_from, og_content, guess_price
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import re

class GenericSitemapProvider:
    def __init__(self, base_url: str, client: HttpClient):
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.source = urlparse(self.base_url).netloc

    def discover_product_urls(self, limit: int = 0) -> List[str]:
        try:
            r = self.client.get(urljoin(self.base_url, "/sitemap.xml"))
            urls = re.findall(r"<loc>(.*?)</loc>", r.text)
        except Exception:
            return []
        product_like = [u for u in urls if any(x in u.lower() for x in ["/product", "/products", "/item", "/p/"])]
        seen=set(); dedup=[]
        for u in product_like:
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
        urls = self.discover_product_urls(limit=limit_pages)
        for u in urls:
            try:
                item = self.parse_product(u)
                if not item["name"]: continue
                if keywords:
                    low = item["name"].lower()
                    if not any(k.lower() in low for k in keywords): continue
                out.append(item)
            except Exception:
                continue
        return out
