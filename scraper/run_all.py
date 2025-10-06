import os, argparse, json, csv
from typing import List, Dict
from urllib.parse import urlparse
from datetime import datetime
from tqdm import tqdm

from providers.base import HttpClient
from providers.shopify_sitemap import ShopifySitemapProvider
from providers.generic_sitemap import GenericSitemapProvider
from providers.heuristic_catalog import HeuristicCatalogProvider
from util import norm_name, make_id

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_csv(path, items: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not items:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("")
        return
    keys = sorted({k for it in items for k in it.keys()})
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for it in items:
            w.writerow(it)

def run_for_site(base_url: str, client: HttpClient, keywords: List[str], limit_per_site: int, log_dir: str) -> List[Dict]:
    logs = []
    def log(msg):
        ts = datetime.utcnow().isoformat()+"Z"
        logs.append(f"[{ts}] {msg}")

    items: List[Dict] = []
    for Provider in [ShopifySitemapProvider, GenericSitemapProvider, HeuristicCatalogProvider]:
        try:
            prov = Provider(base_url, client)
            log(f"Trying {Provider.__name__}")
            got = prov.search(keywords, limit_pages=limit_per_site if limit_per_site>0 else 0)
            log(f"{Provider.__name__} yielded {len(got)} items")
            items.extend(got)
            if len(items) >= 50:  # heuristic break if a provider works well
                break
        except Exception as e:
            log(f"ERROR {Provider.__name__}: {e}")
    dom = urlparse(base_url).netloc
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"{dom}.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(logs))
    return items

def dedupe(items: List[Dict]) -> List[Dict]:
    seen=set(); out=[]
    for it in items:
        key=(norm_name(it.get("name","")), norm_name((it.get("brand") or "")), it.get("source",""))
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
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--delay-ms", type=int, default=700)
    p.add_argument("--user-agent", default=None)
    args = p.parse_args()

    with open(args.sites_file, "r", encoding="utf-8") as f:
        sites=[ln.strip() for ln in f if ln.strip()]

    keywords=[]
    if args.keywords_file and os.path.exists(args.keywords_file):
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords=[ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    client = HttpClient(timeout=args.timeout, delay_ms=args.delay_ms, user_agent=args.user_agent)

    all_raw=[]; per_counts={}
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/combined", exist_ok=True)
    os.makedirs("data/site_reports", exist_ok=True)

    for site in tqdm(sites, desc="Sites"):
        got = run_for_site(site, client, keywords, args.limit_per_site, log_dir="data/site_reports")
        dom = urlparse(site).netloc
        per_counts[dom]=len(got)
        for it in got:
            it.setdefault("currency","EGP")
            it.setdefault("source", dom)
            it["scraped_at"]=datetime.utcnow().isoformat()+"Z"
        write_json(f"data/raw/{dom}.json", got)
        write_csv(f"data/raw/{dom}.csv", got)
        all_raw.extend(got)

    write_json("data/combined/products_raw.json", all_raw)

    clean=[]
    for it in all_raw:
        name=it.get("name"); price=it.get("price_egp"); url=it.get("url"); src=it.get("source")
        if not name or price is None: continue
        if not (args.min_price <= float(price) <= args.max_price): continue
        it["id"]=make_id(src or "", name, float(price), url or "")
        clean.append(it)

    clean=dedupe(clean)
    write_json("data/combined/products_clean.json", clean)
    write_csv("data/combined/products_clean.csv", clean)

    os.makedirs("web/data", exist_ok=True)
    write_json("web/data/products.json", clean)

    report={
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "min_price": args.min_price,
        "max_price": args.max_price,
        "sites": per_counts,
        "total_raw": len(all_raw),
        "total_clean": len(clean),
    }
    write_json("data/run_report.json", report)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
