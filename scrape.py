import json
import os
import pathlib
import requests

STATE_FILE = pathlib.Path("seen.json")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")

# Company registry. Each entry has type in {"greenhouse","lever","ashby","custom"}.
# Slugs verified by hitting each ATS API directly (see CHANGELOG).
COMPANIES = [
    # --- Greenhouse ---
    {"name": "databricks", "type": "greenhouse", "slug": "databricks"},
    {"name": "stripe",     "type": "greenhouse", "slug": "stripe"},
    {"name": "airbnb",     "type": "greenhouse", "slug": "airbnb"},
    {"name": "figma",      "type": "greenhouse", "slug": "figma"},
    {"name": "anthropic",  "type": "greenhouse", "slug": "anthropic"},
    {"name": "discord",    "type": "greenhouse", "slug": "discord"},
    {"name": "robinhood",  "type": "greenhouse", "slug": "robinhood"},
    {"name": "coinbase",   "type": "greenhouse", "slug": "coinbase"},
    {"name": "reddit",     "type": "greenhouse", "slug": "reddit"},
    {"name": "mercury",    "type": "greenhouse", "slug": "mercury"},
    {"name": "pinterest",  "type": "greenhouse", "slug": "pinterest"},
    {"name": "cloudflare", "type": "greenhouse", "slug": "cloudflare"},
    {"name": "affirm",     "type": "greenhouse", "slug": "affirm"},
    {"name": "brex",       "type": "greenhouse", "slug": "brex"},
    {"name": "instacart",  "type": "greenhouse", "slug": "instacart"},
    {"name": "chime",      "type": "greenhouse", "slug": "chime"},
    {"name": "scale",         "type": "greenhouse", "slug": "scaleai"},
    {"name": "asana",         "type": "greenhouse", "slug": "asana"},
    {"name": "twitch",        "type": "greenhouse", "slug": "twitch"},
    {"name": "roblox",        "type": "greenhouse", "slug": "roblox"},
    {"name": "block",         "type": "greenhouse", "slug": "block"},
    {"name": "gemini",        "type": "greenhouse", "slug": "gemini"},
    {"name": "sofi",          "type": "greenhouse", "slug": "sofi"},
    {"name": "marqeta",       "type": "greenhouse", "slug": "marqeta"},
    {"name": "samsara",       "type": "greenhouse", "slug": "samsara"},
    {"name": "rubrik",        "type": "greenhouse", "slug": "rubrik"},
    {"name": "mongodb",       "type": "greenhouse", "slug": "mongodb"},
    {"name": "elastic",       "type": "greenhouse", "slug": "elastic"},
    {"name": "gitlab",        "type": "greenhouse", "slug": "gitlab"},
    {"name": "dropbox",       "type": "greenhouse", "slug": "dropbox"},
    {"name": "lyft",          "type": "greenhouse", "slug": "lyft"},
    {"name": "xai",           "type": "greenhouse", "slug": "xai"},
    {"name": "together",      "type": "greenhouse", "slug": "togetherai"},
    {"name": "spacex",        "type": "greenhouse", "slug": "spacex"},
    {"name": "neuralink",     "type": "greenhouse", "slug": "neuralink"},
    {"name": "cockroachdb",   "type": "greenhouse", "slug": "cockroachlabs"},
    {"name": "ridgeline",     "type": "greenhouse", "slug": "ridgeline"},
    {"name": "squarespace",   "type": "greenhouse", "slug": "squarespace"},

    # --- Ashby ---
    {"name": "linear",     "type": "ashby", "slug": "linear"},
    {"name": "vercel",     "type": "ashby", "slug": "vercel"},
    {"name": "perplexity", "type": "ashby", "slug": "perplexity"},
    {"name": "cursor",     "type": "ashby", "slug": "cursor"},
    {"name": "openai",     "type": "ashby", "slug": "openai"},
    {"name": "ramp",       "type": "ashby", "slug": "ramp"},
    {"name": "plaid",      "type": "ashby", "slug": "plaid"},
    {"name": "snowflake",  "type": "ashby", "slug": "snowflake"},
    {"name": "notion",     "type": "ashby", "slug": "notion"},
    {"name": "harvey",     "type": "ashby", "slug": "harvey"},
    {"name": "sierra",     "type": "ashby", "slug": "sierra"},
    {"name": "cohere",     "type": "ashby", "slug": "cohere"},
    {"name": "characterai","type": "ashby", "slug": "character"},
    {"name": "elevenlabs", "type": "ashby", "slug": "elevenlabs"},
    {"name": "replit",     "type": "ashby", "slug": "replit"},
    {"name": "runway",     "type": "ashby", "slug": "runway"},
    {"name": "polymarket", "type": "ashby", "slug": "polymarket"},
    {"name": "kalshi",     "type": "ashby", "slug": "kalshi"},

    # --- Lever ---
    {"name": "netflix",    "type": "lever", "slug": "netflix"},
    {"name": "palantir",   "type": "lever", "slug": "palantir"},
    {"name": "mistral",    "type": "lever", "slug": "mistral"},

    # --- Custom (Workday / bespoke career sites — scrapers not yet implemented) ---
    {"name": "doordash",   "type": "custom", "fn": "scrape_doordash"},
    {"name": "datadog",    "type": "custom", "fn": "scrape_datadog"},
    {"name": "rippling",   "type": "custom", "fn": "scrape_rippling"},
    {"name": "google",     "type": "custom", "fn": "scrape_google"},
    {"name": "meta",       "type": "custom", "fn": "scrape_meta"},
    {"name": "apple",      "type": "custom", "fn": "scrape_apple"},
    {"name": "amazon",     "type": "custom", "fn": "scrape_amazon"},
    {"name": "nvidia",     "type": "custom", "fn": "scrape_nvidia"},
]

# Companies to temporarily skip without deleting from COMPANIES.
COMPANIES_DISABLED = set()

INCLUDE_KEYWORDS = [
    "intern", "internship",
    "software engineer", "software engineering",
    "software developer", "software development",
    "data engineer", "data engineering",
    "machine learning", "ml engineer",
    "ai engineer", "artificial intelligence",
    "technical",
    "engineer", "engineering",
    "developer",
]

EXCLUDE_KEYWORDS = [
    "senior", "staff", "principal",
    "director", "manager", "head of",
    "vice president",
]


def matches_keywords(title: str) -> bool:
    t = title.lower()
    if any(ex in t for ex in EXCLUDE_KEYWORDS):
        return False
    return any(inc in t for inc in INCLUDE_KEYWORDS)


def scrape_greenhouse(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company['slug']}/jobs"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return [
        {
            "id": f"gh-{company['slug']}-{j['id']}",
            "company": company["name"],
            "title": j["title"],
            "url": j["absolute_url"],
        }
        for j in r.json().get("jobs", [])
        if matches_keywords(j["title"])
    ]


def scrape_lever(company):
    url = f"https://api.lever.co/v0/postings/{company['slug']}?mode=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return [
        {
            "id": f"lv-{company['slug']}-{j['id']}",
            "company": company["name"],
            "title": j["text"],
            "url": j["hostedUrl"],
        }
        for j in r.json()
        if matches_keywords(j["text"])
    ]


def scrape_ashby(company):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company['slug']}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return [
        {
            "id": f"ab-{company['slug']}-{j['id']}",
            "company": company["name"],
            "title": j["title"],
            "url": j["jobUrl"],
        }
        for j in r.json().get("jobs", [])
        if matches_keywords(j["title"])
    ]


SCRAPERS = {
    "greenhouse": scrape_greenhouse,
    "lever":      scrape_lever,
    "ashby":      scrape_ashby,
}


# --- Custom scraper stubs. Each needs a bespoke scraper (Workday/careers page). ---
def scrape_doordash(): return []   # TODO: careers.doordash.com (Workday)
def scrape_datadog():  return []   # TODO: careers.datadoghq.com (Workday)
def scrape_rippling(): return []   # TODO: rippling.com/careers (Workday)
def scrape_google():   return []   # TODO: google.com/about/careers/applications/jobs/results
def scrape_meta():     return []   # TODO: metacareers.com
def scrape_apple():    return []   # TODO: jobs.apple.com
def scrape_amazon():   return []   # TODO: amazon.jobs
def scrape_nvidia():   return []   # TODO: nvidia.wd5.myworkdayjobs.com


def notify(job):
    if not NTFY_TOPIC:
        print(f"[dry-run] would notify: {job['company']} — {job['title']}")
        return
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=f"{job['company'].upper()}: {job['title']}".encode(),
        headers={
            "Title": "New job posted",
            "Priority": "high",
            "Click": job["url"],
            "Tags": "briefcase",
        },
    )


def main():
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        seen_ids = set(state.get("ids", []))
        first_run = bool(state.get("seed_run", False))
    else:
        seen_ids = set()
        first_run = True

    all_jobs = []
    for company in COMPANIES:
        if company["name"] in COMPANIES_DISABLED:
            print(f"{company['name']}: [disabled]")
            continue
        try:
            if company["type"] == "custom":
                jobs = globals()[company["fn"]]()
            else:
                jobs = SCRAPERS[company["type"]](company)
        except Exception as e:
            print(f"[error] {company['name']}: {e}")
            continue
        print(f"{company['name']}: {len(jobs)} matching roles")
        all_jobs.extend(jobs)

    new_jobs = [j for j in all_jobs if j["id"] not in seen_ids]

    if first_run:
        print(f"[first run] found {len(all_jobs)} jobs, not sending notifications")
    else:
        print(f"found {len(new_jobs)} NEW jobs")
        for job in new_jobs:
            print(f"  NEW: {job['company']} — {job['title']}")
            notify(job)

    all_ids = list({j["id"] for j in all_jobs})
    STATE_FILE.write_text(json.dumps({"ids": all_ids}, indent=2))


if __name__ == "__main__":
    main()
