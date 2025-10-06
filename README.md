# Edith – Egypt Gaming Accessories Scraper (GitHub-ready)

This repo scrapes **15 Egyptian** e-commerce sites for gaming accessories, normalizes prices to **EGP**, filters **EGP 100 → 2500**, and commits **raw + combined** data back to the repository.
A small viewer in `web/` lets you preview `web/data/products.json`.

**Websites**
- https://www.games2egypt.com
- https://shamystores.com
- https://www.gamesworldegypt.com
- https://egygamer.com
- https://thegamecaveegypt.com
- https://gamerscolony.net
- https://egyptlaptop.com
- https://compume.com.eg
- https://www.compumarts.com
- https://hardwaremarket.net
- https://ahw.store
- https://www.pcs-souq.com
- https://rabbitstore-eg.com
- https://tv-it.com
- https://egyptgamestore.com

---

## 1) Upload to GitHub (first time)
1. Create a **new GitHub repo** (public or private).
2. Download the release ZIP from ChatGPT and **upload/extract** its contents into the repo (or push via Git).
3. Commit and push.

> Nothing else to configure. The workflow uses the built-in `GITHUB_TOKEN` and has `permissions: contents: write` to commit data files.

---

## 2) Run from Actions tab
- Go to **Actions → “Scrape & Publish (Egypt Gaming)” → Run workflow**.
- Inputs:
  - `limit_per_site`: `0` = unlimited (default)
  - `min_price`: `100`
  - `max_price`: `2500`
- It also runs daily at **08:00 Africa/Cairo**.

On success, the workflow commits:
- `data/raw/<domain>.json` & `.csv` (per site, raw)
- `data/combined/products_raw.json`
- `data/combined/products_clean.json` & `.csv` (filtered 100–2500 EGP, de-duplicated)
- `web/data/products.json` (used by the viewer)
- `data/site_reports/<domain>.log` and `data/run_report.json`

---

## 3) Preview data (optional)
Serve locally:
```bash
python -m http.server 4000
# open http://localhost:4000/web/
```

---

## Notes & tips
- Some stores may block bots or omit product metadata in sitemaps/OG tags. The repo tries **three strategies**:
  1. Shopify product sitemaps
  2. Generic sitemaps with product-like URLs
  3. Heuristic: pick “producty” links on the homepage and parse OpenGraph / price blocks
- For stubborn sites, add site-specific selectors in a custom provider later.
- To throttle harder, edit `scraper/scrape_config.yaml` (delay/timeout).

— Built by **Edith**.
