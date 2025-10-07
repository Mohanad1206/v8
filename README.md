# Edith – Egypt Gaming Accessories Scraper (GitHub-ready)

A scraper-only toolkit that gathers gaming accessory products from multiple Egyptian e‑commerce stores, normalizes prices to **EGP**, filters within a target range, and **commits results back to the same repository** via GitHub Actions. It includes a minimal web viewer to browse the merged dataset.

## Key features
- Multi-strategy scraping (sitemaps → heuristics → optional dynamic rendering via Playwright).
- **Dynamic mode**: `auto` (fallback when static is weak), `always`, or `never`.
- **Proxy hooks** via env (`HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`) — pass one as a GitHub secret to improve reliability.
- Outputs saved **inside the repo** so you can inspect raw JSON/CSV before any downstream processing.
- Small front-end viewer in `web/` for quick product browsing.

## Output files & schema
All CSV/JSON exports follow **this exact column order** and names:

`id, product name, product price, currency, product url, site name, time stamp`

Folders:
- `data/raw/<domain>.{json,csv}` – Per‑site exports
- `data/combined/products_raw.{json,csv}` – All sites (unfiltered)
- `data/combined/products_clean.{json,csv}` – Filtered & de‑duplicated
- `data/site_reports/<domain>.log` – Per‑site logs
- `data/run_report.json` – Summary (counts, mode, etc.)
- `web/data/products.json` – Dataset for the demo viewer (fields optimized for the UI)

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r scraper/requirements.txt
python -m playwright install --with-deps            # for dynamic rendering

# Scrape all sites, allow dynamic fallback, filter 100–2500 EGP
python scraper/run_all.py --sites-file scraper/sites.txt --min-price 100 --max-price 2500 --limit-per-site 0 --dynamic-mode auto

# Preview the dataset
python -m http.server 4000
# open http://localhost:4000/web/
```

## Run on GitHub Actions
1. Create a new GitHub repository and push these files.
2. (Optional) Add a secret `SCRAPER_PROXY_URL` if you want to route through a proxy.
3. Go to **Actions → “Scrape & Publish (Egypt Gaming)” → Run workflow** and set inputs:
   - `limit_per_site`: `0` = unlimited (default)
   - `min_price`: `100`
   - `max_price`: `2500`
   - `dynamic_mode`: `auto` | `never` | `always`
4. The workflow commits updated CSV/JSON to `data/…` and the viewer dataset to `web/data/products.json`.

## Notes
- Respect each site’s Terms and robots rules; tune `scraper/scrape_config.yaml` for delays/timeouts.
- If a site still yields no data, try `dynamic_mode=always` and/or configure a proxy. For particularly stubborn stores, add site‑specific selectors in a custom provider.
