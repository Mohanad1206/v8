from .base import HttpClient, soup_from, og_content, guess_price
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import re
SA
                r = self.client.get(urljoin(self.base_url, path))
                soup = soup_from(r)
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                        continue
                    full = urljoin(self.base_url, href)
                    low = full.lower()
                    if any(p in low for p in ["/product/", "/products/", "/item/", "/p/", "/gaming/", "/keyboard", "/mouse", "/headset"]):
                        urls.append(full)
            except Exception:
                continue
        # Also try homepage
        try:
            r = self.client.get(self.base_url)
            soup = soup_from(r)
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                full = urljoin(self.base_url, href)
                low = full.lower()
                if any(p in low for p in ["/product/", "/products/", "/item/", "/p/", "/gaming/", "/keyboard", "/mouse", "/headset"]):
                    urls.append(full)
        except Exception:
            pass
        # Deduplicate
        seen = set()
        dedup = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                dedup.append(u)
        return dedup if limit == 0 else dedup[:limit]

    def parse_product(self, url: str) -> Dict:
        r = self.client.get(url)
        soup = soup_from(r)
        title = og_content(soup, "og:title") or (soup.title.string if soup.title else "")
        price = guess_price(soup)
        img = og_content(soup, "og:image") or ""
        brand = og_content(soup, "product:brand")
        # Try to extract category from breadcrumbs or schema
        category = None
        breadcrumbs = soup.select("[class*=breadcrumb], [id*=breadcrumb]")
        if breadcrumbs:
            cats = [el.get_text(strip=True) for el in breadcrumbs[0].find_all("a")]
            if cats:
                category = " > ".join(cats[-2:])  # Last two levels
        return {"name": title.strip(), "price_egp": float(price) if price is not None else None, "currency": "EGP", "url": url, "image_url": img, "brand": brand, "category": category, "source": self.source}

    def search(self, keywords: List[str], limit_pages: int = 0) -> List[Dict]:
        out = []
        urls = self.discover_product_urls(limit=limit_pages)
        for u in urls:
            try:
                item = self.parse_product(u)
                if not item["name"]:
                    continue
                if keywords:
                    low = item["name"].lower()
                    if not any(k.lower() in low for k in keywords):
                        continue
                out.append(item)
            except Exception:
                continue
        return out
