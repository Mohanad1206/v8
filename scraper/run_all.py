
import os, argparse, json, csv, sys
from typing import List, Dict
from urllib.parse import urlparse
from datetime import datetime
from tqdm import tqdm

from providers.base import HttpClient
from providers.shopify_sitemap import ShopifySitemapProvider
from providers.generic_sitemap import GenericSitemapProvider
from providers.heuristic_catalog import HeuristicCatalogProvider

def get_dynamic_provider():
    try:
        from providers.playwright_dynamic import PlaywrightDynamicProvider
        return PlaywrightDynamicProvider
    except Exception:
        return None

from util import norm_name, make_id

# Desired export columns in exact order
EXPORT_COLUMNS = ["id", "product name", "product price", "currency", "product url", "site name", "time stamp"]

def to_export_row(it: Dict) -> Dict:
    """Map internal item -> strict ordered export row with required keys only."""
    return {
        "id": it.get("id") or "",
        "product name": it.get("name") or "",
        "product price": it.get("price_egp", None),
        "currency": it.get("currency") or "EGP",
        "product url": it.get("url") or "",
        "site name": it.get("source") or "",
        "time stamp": it.get("scraped_at") or "",
    }

def write_json(path, items: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def write_csv(path, items: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        w.writeheader()
        for it in items:
            w.writerow(it)

def run_for_site(base_url: str, client: HttpClient, keywords: List[str], limit_per_site: int, log_dir: str, dynamic_mode: str) -> List[Dict]:
    logs = []
    def log(msg):
        ts = datetime.utcnow().isoformat()+"Z"
        logs.append(f"[{ts}] {msg}")

    items: List[Dict] = []
    def try_static():
        for Provider in [ShopifySitemapProvider, GenericSitemapProvider, HeuristicCatalogProvider]:
            try:
                prov = Provider(base_url, client)
                log(f"Trying {Provider.__name__}")
                got = prov.search(keywords, limit_pages=limit_per_site if limit_per_site>0 else 0)
                log(f"{Provider.__name__} yielded {len(got)} items")
                items.extend(got)
                if len(items) >= 50:
                    break
            except Exception as e:
                log(f"ERROR {Provider.__name__}: {e}")

    dyn_cls = get_dynamic_provider()

    if dynamic_mode == "always" and dyn_cls:
        try:
            log("Dynamic mode = always. Using Playwright first.")
            prov = dyn_cls(base_url)
            got = prov.search(keywords, limit_pages=limit_per_site if limit_per_site>0 else 0)
            log(f"PlaywrightDynamicProvider yielded {len(got)} items")
            items.extend(got)
        except Exception as e:
            log(f"ERROR PlaywrightDynamicProvider: {e}")
        if len(items) < 50:
            try_static()
    else:
        try_static()
        if dyn_cls and (dynamic_mode == "auto") and len(items) < 10:
            try:
                log("Static yielded few/none; falling back to PlaywrightDynamicProvider.")
                prov = dyn_cls(base_url)
                got = prov.search(keywords, limit_pages=limit_per_site if limit_per_site>0 else 0)
                log(f"PlaywrightDynamicProvider yielded {len(got)} items")
                items.extend(got)
            except Exception as e:
                log(f"ERROR PlaywrightDynamicProvider: {e}")

    dom = urlparse(base_url).netloc
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"{dom}.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(logs))

    now = datetime.utcnow().isoformat()+"Z"
    # annotate + ensure id for *all* items
    for it in items:
        it.setdefault("source", dom)
        it.setdefault("currency", "EGP")
        it["scraped_at"] = now
        it["id"] = make_id(it.get("source",""), it.get("name",""), it.get("price_egp"), it.get("url",""))
        # DO NOT include brand/category in exports; keep them internal only (not used below).

    return items

def dedupe(items: List[Dict]) -> List[Dict]:
    seen=set(); out=[]
    for it in items:
        key=(it.get("id") or norm_name(it.get("name","")), it.get("source",""))
        if key in seen: continue
        seen.add(key); out.append(it)
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sites-file", default="scraper/sites.txt")
    p.add_argument("--keywords-file", default=None)
    p.add_argument("--min-price", type=float, default=100.0)
    p.add_argument("--max-price", type=float, default=2500.0)
    p.add_argument("--limit-per-site", type=int, default=0, help="0 = unlimited")
    p.add_argument("--timeout", type=int, default=25)
    p.add_argument("--delay-ms", type=int, default=900)
    p.add_argument("--user-agent", default=None)
    p.add_argument("--dynamic-mode", default=os.getenv("SCRAPER_DYNAMIC_MODE","auto"), choices=["auto","never","always"])
    args = p.parse_args()

    with open(args.sites_file, "r", encoding="utf-8") as f:
        sites=[ln.strip() for ln in f if ln.strip()]

    keywords=[]
    if args.keywords_file and os.path.exists(args.keywords_file):
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords=[ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    client = HttpClient(timeout=args.timeout, delay_ms=args.delay_ms, user_agent=args.user_agent)

    all_items=[]; per_counts={}
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/combined", exist_ok=True)
    os.makedirs("data/site_reports", exist_ok=True)

    # Collect site items (internal, rich), but write per-site exports in strict order
    for site in tqdm(sites, desc="Sites"):
        got = run_for_site(site, client, keywords, args.limit_per_site, log_dir="data/site_reports", dynamic_mode=args.dynamic_mode)
        dom = urlparse(site).netloc
        per_counts[dom]=len(got)

        # Per-site exports (CSV/JSON) with strict schema
        export_rows = [to_export_row(it) for it in got]
        write_json(f"data/raw/{dom}.json", export_rows)
        write_csv(f"data/raw/{dom}.csv", export_rows)

        all_items.extend(got)

    # Combined RAW (still strict schema)
    combined_export = [to_export_row(it) for it in all_items]
    write_json("data/combined/products_raw.json", combined_export)
    write_csv("data/combined/products_raw.csv", combined_export)

    # Clean: price within range, non-empty name
    clean_internal=[]
    for it in all_items:
        price = it.get("price_egp")
        if price is None: 
            continue
        if not (args.min_price <= float(price) <= args.max_price):
            continue
        if not it.get("name"): 
            continue
        clean_internal.append(it)

    clean_internal = dedupe(clean_internal)

    # Combined CLEAN (strict schema)
    clean_export = [to_export_row(it) for it in clean_internal]
    write_json("data/combined/products_clean.json", clean_export)
    write_csv("data/combined/products_clean.csv", clean_export)

    # Front-end dataset (can keep richer fields for the viewer)
    os.makedirs("web/data", exist_ok=True)
    # Minimal viewer data: keep name, price, url, image, source
    view = [{
        "id": it.get("id"),
        "name": it.get("name"),
        "price_egp": it.get("price_egp"),
        "currency": it.get("currency","EGP"),
        "url": it.get("url"),
        "image_url": it.get("image_url",""),
        "source": it.get("source"),
        "scraped_at": it.get("scraped_at"),
    } for it in clean_internal]
    with open("web/data/products.json", "w", encoding="utf-8") as f:
        json.dump(view, f, ensure_ascii=False, indent=2)

    report={
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "min_price": args.min_price,
        "max_price": args.max_price,
        "sites": per_counts,
        "total_raw": len(all_items),
        "total_clean": len(clean_internal),
        "dynamic_mode": args.dynamic_mode,
    }
    with open("data/run_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
