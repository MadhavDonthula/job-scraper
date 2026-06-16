# Job Scraper — Full Setup Guide

A scraper that checks ~80 tech companies for new internship/SWE postings and pushes
them to your iPhone, running 24/7 in the cloud (no laptop needed).

This guide walks you through replicating it from a fork of this repo.

---

## Part 1 — Get the code (fork this repo)

1. Click **Fork** (top-right of this repo) → **Create fork**. You now have your own copy
   at `github.com/YOUR_USERNAME/job-scraper`, including all the scraper code and the
   GitHub Actions workflow.
2. *(Optional — only if you want to test locally too)* Clone it:
   ```bash
   git clone https://github.com/YOUR_USERNAME/job-scraper.git
   cd job-scraper
   ```

> Forking is the key step — you need a repo **you own** so Actions can commit its state
> (`seen.json`) back. You inherit the seeded `seen.json`, so you won't get flooded —
> only genuinely new postings will alert.

---

## Part 2 — Set up notifications on your iPhone (ntfy)

1. Install the **ntfy** app: https://apps.apple.com/app/ntfy/id1625396347
2. **Pick your own unique topic name** — anything hard to guess, e.g.
   `friendname-jobs-7x9k2p`. **Do NOT reuse someone else's topic** or you'll both get
   each other's alerts.
3. In the app: tap **+** → enter your topic → **Subscribe**.
4. **Critical iOS settings (these are what trip everyone up):**
   - **Settings → Notifications → ntfy** → **Allow Notifications ON**; enable
     **Lock Screen / Banners / Sounds**.
   - **Settings → Notifications → Scheduled Summary** → make sure **ntfy is NOT in it**
     (this silently delays notifications — the #1 gotcha).
   - **Settings → Battery → Low Power Mode OFF**.
   - In the ntfy app, make sure the topic isn't muted (bell icon, not bell-with-slash).

---

## Part 3 — Test locally *(optional but recommended)*

Requires **Python 3.10 or newer** (the code uses modern type syntax — 3.9 will crash).
On Mac: `brew install python@3.13`.

```bash
cd job-scraper
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# dry run — prints what it WOULD send, no notifications
python3 scrape.py

# real run — pushes to your phone
export NTFY_TOPIC="YOUR_TOPIC"
python3 scrape.py
```

If your phone buzzes, the pipeline works. (On Windows: `py -3.13 -m venv .venv` then
`.venv\Scripts\activate`.)

---

## Part 4 — Enable the cloud (GitHub Actions)

1. On your fork, go to the **Actions** tab → click
   **"I understand my workflows, enable them."** (Forks have Actions off by default.)
2. Make sure the repo is **Public** (Settings → General). Public = free unlimited Actions.
3. Add your ntfy topic as a secret:
   - **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `NTFY_TOPIC`
   - Value: `YOUR_TOPIC`
4. Test it: **Actions tab → "scrape-jobs" → Run workflow → Run workflow**. After ~40s it
   should complete green, and any new jobs ping your phone.

The workflow file is already in the repo (`.github/workflows/scrape.yml`).

---

## Part 5 — Make it run reliably every 5 min (cron-job.org)

GitHub's built-in scheduler is unreliable (it may fire only once an hour). An external
scheduler forces it on time.

### 5a. Create a GitHub token
1. Go to https://github.com/settings/personal-access-tokens/new (fine-grained token).
2. **Name:** `job-scraper-cron` · **Expiration:** pick a long one (e.g. 1 year).
3. **Resource owner:** your username · **Repository access:** Only select repositories →
   **`job-scraper`**.
4. **Permissions → Repository → Actions → Read and write.** (Leave everything else default.)
5. **Generate token** and copy it — it starts with `github_pat_...`.

### 5b. Set up cron-job.org
1. Make a free account at https://cron-job.org → **Create cronjob**.
2. **Title:** `job-scraper trigger`
3. **URL** (replace `YOUR_USERNAME`):
   ```
   https://api.github.com/repos/YOUR_USERNAME/job-scraper/actions/workflows/scrape.yml/dispatches
   ```
   *(It may show a red "URL not valid" warning — ignore it; that's just cron-job.org
   probing with a GET.)*
4. **Schedule:** Every **5 minutes**.
5. Open **Advanced**:
   - **Request method:** `POST`
   - **Request body:** `{"ref":"main"}`
   - **Headers** — add these **four** as separate Key / Value rows:

   | Key | Value |
   |---|---|
   | `Authorization` | `Bearer github_pat_YOURTOKEN` |
   | `Accept` | `application/vnd.github+json` |
   | `X-GitHub-Api-Version` | `2022-11-28` |
   | `Content-Type` | `application/json` |

   > ⚠️ **Common mistake:** the value is `Bearer ` + your token. Your token *already*
   > starts with `github_pat_`, so it should read `Bearer github_pat_...` —
   > **only one** `github_pat_`. Two of them = 404.

6. Click **TEST RUN**. You want **`204 No Content`** = success.
   (404 = bad token or wrong method; 401 = missing `Bearer`.)
7. **Save.**

---

## Part 6 — Verify it's live

- On cron-job.org, the job shows successful executions every 5 min.
- On GitHub → **Actions** tab, runs appear every ~5 minutes.
- New internship postings now push to your phone automatically, 24/7.

---

## Notes & gotchas

- **Use your own topic + your own token** — don't copy anyone else's.
- **iOS Scheduled Summary** is the most common reason "notifications don't show" —
  re-check Part 2, step 4.
- **Token expiry:** your PAT expires on the date you set — when it does, alerts stop.
  Regenerate it and update the `Authorization` header in cron-job.org.
- **Never share screenshots of the token** — it's a password.
- **Customize companies:** edit the `COMPANIES` list in `scrape.py`, commit, push — the
  cloud picks it up automatically.
