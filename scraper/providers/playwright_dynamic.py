from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import re, os, contextlib

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup


def og_content(soup: BeautifulSoup, prop: str) -> Optional[str]:
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return tag["content"].strip() if tag and tag.get("content") else None


def guess_price(soup: BeautifulSoup) -> Optional[float]:
    for prop in ["product:price:amount", "og:price:amount"]:
        c = og_content(soup, prop)
        if c:
            try: return float(c.replace(",", ""))
            except: pass
    cand = soup.select("[class*=price], [id*=price]")
    for el in cand[:12]:
        txt = el.get_text(" ", strip=True).replace(",", "")
        m = re.search(r'(\d{2,6}(?:[.,]\d{2})?)', txt)
        if m:
            try: return float(m.group(1))
            except: pass
    return None


class PlaywrightDynamicProvider:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.source = urlparse(self.base_url).netloc
        self.proxy = os.getenv("ALL_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    def _launch(self):
        pw = sync_playwright().start()
        launch_args = {"headless": True}
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}
        browser = pw.chromium.launch(**launch_args)
        ctx = browser.new_context(locale="en-EG", user_agent=os.getenv("SCRAPER_USER_AGENT", None))
        stealth_sync(ctx)
        page = ctx.new_page()
        return pw, browser, ctx, page

    def _close(self, pw, browser, ctx):
        with contextlib.suppress(Exception):
            ctx.close()
        with contextlib.suppress(Exception):
            browser.close()
        with contextlib.suppress(Exception):
            pw.stop()

    def _render(self, url: str) -> Optional[str]:
        pw, browser, ctx, page = self._launch()
        html = None
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=35000)
            with contextlib.suppress(Exception):
                page.wait_for_selector("meta[property='og:title'], [class*=price], [id*=price]", timeout=8000)
            html = page.content()
        finally:
            self._close(pw, browser, ctx)
        return html

    def discover_product_urls(self, limit: int = 0) -> List[str]:
        urls: List[str] = []
        html = self._render(self.base_url + "/sitemap.xml")
        if html:
            urls += re.findall(r"<loc>(.*?)</loc>", html)
        urls = [u for u in urls if "/product" in u.lower() or "/products/" in u.lower() or "/item/" in u.lower()]
        if not urls:
            html = self._render(self.base_url)
            if html:
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                        continue
                    full = urljoin(self.base_url, href)
                    low = full.lower()
                    if any(h in low for h in ["product","products","item","p/","gaming","keyboard","mouse","headset"]):
                        urls.append(full)
        seen=set(); dedup=[]
        for u in urls:
            if u in seen: continue
            seen.add(u); dedup.append(u)
        return dedup if limit == 0 else dedup[:limit]

    def parse_product(self, url: str) -> Dict:
        html = self._render(url)
        if not html:
            return {}
        soup = BeautifulSoup(html, "lxml")
        title = og_content(soup, "og:title") or (soup.title.string if soup.title else "")
        price = guess_price(soup)
        img = og_content(soup, "og:image") or ""
        return {"name": (title or "").strip(), "price_egp": float(price) if price is not None else None, "currency": "EGP", "url": url, "image_url": img, "brand": og_content(soup, "product:brand"), "category": None, "source": self.source}

    def search(self, keywords: List[str], limit_pages: int = 0) -> List[Dict]:
        out = []
        urls = self.discover_product_urls(limit=limit_pages)
        for u in urls:
            try:
                item = self.parse_product(u)
                if not item or not item.get("name"):
                    continue
                if keywords:
                    low = item["name"].lower()
                    if not any(k.lower() in low for k in keywords):
                        continue
                out.append(item)
            except Exception:
                continue
        return out
