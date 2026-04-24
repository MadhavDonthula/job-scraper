# Changelog

## 2026-04-23

### Task 1 — Reset seen.json
- Verified `seen.json` is absent from both local and `origin/main`. No action needed; first-run guard in `main()` will create a fresh baseline on the next Actions run without firing notifications.

### Task 2 — Keyword filter rewrite
- Replaced narrow `KEYWORDS = ["software engineer", "swe", "software development"]` with a broad `INCLUDE_KEYWORDS` set covering intern/early-career SWE, data, ML/AI, and generic "engineer"/"developer"/"technical".
- Added `EXCLUDE_KEYWORDS` (senior/staff/principal/director/manager/head of/vice president) so senior roles don't leak through the broad includes.
- `matches_keywords` now: excludes first, then includes. Case-insensitive substring match (no word boundaries — simple + catches most variants).

### Task 4 — Multi-ATS refactor
- Each company now has a `type` (`greenhouse` | `lever` | `ashby` | `custom`). `SCRAPERS` dict dispatches to `scrape_greenhouse` / `scrape_lever` / `scrape_ashby`.
- `custom` entries reference a function name via `"fn"`, resolved through `globals()`. Stubs return `[]` for now (doordash, datadog, rippling, google, meta, apple, amazon, nvidia).
- Per-company failures are caught in `main()` — one broken slug no longer kills the whole run.
- ID prefix convention: `gh-` / `lv-` / `ab-` (plus future custom prefixes per scraper).
- `notify()` and workflow yml untouched per brief.

### Task 3 — Expanded company list
- Greenhouse additions (verified 200 + non-zero job count): cloudflare, affirm, brex, instacart, chime, scaleai, asana, twitch.
- Slug corrections — these were Greenhouse in the prior list but actually 404 there; moved to Ashby (verified): **ramp, plaid, snowflake, notion**. The old list was silently dropping these via the try/except.
- Ashby additions: linear, vercel, perplexity, cursor, openai.
- Lever additions: netflix, palantir.
- Custom stubs: doordash, datadog, rippling (Workday-based; no standard API), plus google/meta/apple/amazon/nvidia per brief.
- Microsoft intentionally skipped (offer already in hand).
- Quant shops (jane street, citadel, etc.) deferred to a later phase per brief.
- `COMPANIES_DISABLED = set()` added so a company can be muted without deletion.

## 2026-04-23 (second batch)

### Expanded company list — round 2
Added 29 verified companies (all hit via live API calls, non-zero match counts confirmed locally):

- **Greenhouse (+19):** roblox, block (Square/Cash App), gemini, sofi, marqeta, samsara, rubrik, mongodb, elastic, gitlab, dropbox, lyft, xai, together (togetherai), spacex, neuralink, cockroachdb (cockroachlabs), ridgeline, squarespace.
- **Ashby (+9):** harvey, sierra, cohere, characterai, elevenlabs, replit, runway, polymarket, kalshi.
- **Lever (+1):** mistral.

Local test: 2758 matching roles across 59 companies, 0 errors. SpaceX alone contributes 815 (giant engineering org; expected).

### Task 5a — SimplifyJobs community feed
- New scraper type `simplify` reads https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json (~20k records, ~15MB per fetch).
- One `simplify-bigtech` entry filters the feed to big tech whose own boards are too painful to scrape directly (Google batchexecute, Meta GraphQL, Apple/Nvidia Workday, TikTok/ByteDance). Amazon included here since we're not building a direct scraper for now.
- Each record honored for `active` + `is_visible`, then put through the same `matches_keywords()` filter as other sources.
- ID prefix `simplify-<uuid>`.
- Dropped the now-redundant `scrape_google` / `scrape_meta` / `scrape_apple` / `scrape_amazon` / `scrape_nvidia` stubs and their COMPANIES entries.
- Local test: simplify-bigtech contributes 215 matches (TikTok 128, ByteDance 32, Meta 21, NVIDIA 12, Netflix 8, Amazon 8, Apple 6, Google 0). Notification latency for these companies now ~1-2h (Simplify contributor lag) + ~10min (our cron) = tolerable for FAANG-class postings with wide windows.

### Expanded simplify-bigtech filter_to (MSFT+ tier)
- Added 25 more target companies to the Simplify filter, covering any MSFT-or-better company we don't already scrape directly.
- Rolled doordash/datadog/rippling into Simplify coverage — dropped their individual custom stubs and the `scrape_doordash/datadog/rippling` functions. Also removed the now-unused `custom` type branch in `main()`.
- New filter_to list (33 companies): google, meta, apple, amazon, nvidia, tiktok, bytedance, netflix; doordash, datadog, rippling; adobe, salesforce, servicenow; intel, amd, qualcomm; tesla, uber, shopify, spotify, snap; waymo, zoox, cruise, figure, anduril; crowdstrike, palo alto networks; airtable, duolingo, riot games, tenstorrent.
- Many currently 0 active (off-season, April 2026); wired in now so they auto-cover when summer-2027 postings open ~July 2026. Local test: simplify-bigtech 273 matches. Total 3025 across all sources.
