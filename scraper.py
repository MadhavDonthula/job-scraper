import json
import os
import pathlib
import requests

STATE_FILE = pathlib.Path("seen.json")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")

# Pilot list — all Greenhouse, all should work out of the box.
# Verify the slug by visiting boards.greenhouse.io/{slug} in your browser.
COMPANIES = [
    {"name": "databricks", "slug": "databricks"},
    {"name": "stripe",     "slug": "stripe"},
    {"name": "airbnb",     "slug": "airbnb"},
    {"name": "figma",      "slug": "figma"},
    {"name": "anthropic",  "slug": "anthropic"},
    {"name": "ramp",       "slug": "ramp"},
    {"name": "discord",    "slug": "discord"},
    {"name": "robinhood",  "slug": "robinhood"},
    {"name": "coinbase",   "slug": "coinbase"},
    {"name": "reddit",     "slug": "reddit"},
    {"name": "plaid",      "slug": "plaid"},
    {"name": "mercury",    "slug": "mercury"},
    {"name": "doordash",   "slug": "doordash"},
    {"name": "pinterest",  "slug": "pinterest"},
    {"name": "datadog",    "slug": "datadoghq"},
]

# What counts as a "match" — tune these over time.
KEYWORDS = ["software engineer", "swe", "software development"]


def matches_keywords(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def scrape_greenhouse(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company['slug']}/jobs"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[error] {company['name']}: {e}")
        return []

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
    # Load what we've seen before
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        seen_ids = set(state.get("ids", []))
        first_run = False
    else:
        seen_ids = set()
        first_run = True

    # Scrape all companies
    all_jobs = []
    for company in COMPANIES:
        jobs = scrape_greenhouse(company)
        print(f"{company['name']}: {len(jobs)} matching roles")
        all_jobs.extend(jobs)

    # Find new ones
    new_jobs = [j for j in all_jobs if j["id"] not in seen_ids]

    # First run: record state, don't spam notifications
    if first_run:
        print(f"[first run] found {len(all_jobs)} jobs, not sending notifications")
    else:
        print(f"found {len(new_jobs)} NEW jobs")
        for job in new_jobs:
            print(f"  NEW: {job['company']} — {job['title']}")
            notify(job)

    # Save state
    all_ids = list({j["id"] for j in all_jobs})
    STATE_FILE.write_text(json.dumps({"ids": all_ids}, indent=2))


if __name__ == "__main__":
    main()