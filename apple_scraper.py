"""
Apple Careers job scraper.

Three-step flow:
  1. GET the careers page so the session picks up the `jobs` cookie
  2. GET /api/v1/CSRFToken — token returned in the `X-Apple-CSRF-Token` response
     header (NOT the body, which is empty)
  3. POST /api/v1/search with the token + JSON body. Paginate until done.

`query="internship"` narrows from ~1400 false positives (any role mentioning
"intern" in the description, e.g. "International Tax Manager") to ~44 real
intern listings. Server-side filtering is much cheaper than pulling everything.
"""

import requests


CAREERS_NAV_URL = "https://jobs.apple.com/en-us/search"
CSRF_URL = "https://jobs.apple.com/api/v1/CSRFToken"
SEARCH_URL = "https://jobs.apple.com/api/v1/search"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)

PAGE_SIZE = 20  # Apple's API returns up to 20 per page; not configurable.


def _prime_session(session: requests.Session) -> None:
    """Hit the careers HTML page so the session picks up `jobs` and `cs-id`
    cookies. Apple's CSRFToken endpoint will mint a fresh token without these,
    but the search endpoint sometimes 403s if the session looks bare."""
    session.get(
        CAREERS_NAV_URL,
        headers={
            "user-agent": USER_AGENT,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        },
        timeout=15,
    )


def _get_csrf_token(session: requests.Session) -> str:
    resp = session.get(
        CSRF_URL,
        headers={
            "user-agent": USER_AGENT,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": CAREERS_NAV_URL,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.headers.get("X-Apple-CSRF-Token")
    if not token:
        raise RuntimeError(
            "X-Apple-CSRF-Token header missing from CSRFToken response. "
            "Apple may have changed their auth flow."
        )
    return token


def _search_page(
    session: requests.Session, csrf_token: str, page: int, query: str = "internship"
) -> dict:
    body = {
        "query": query,
        "filters": {"locations": ["postLocation-USA"]},
        "page": page,
        "locale": "en-us",
        "sort": "relevance",
        "format": {"longDate": "MMMM D, YYYY", "mediumDate": "MMM D, YYYY"},
    }
    resp = session.post(
        SEARCH_URL,
        headers={
            "user-agent": USER_AGENT,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "browserlocale": "en-us",
            "content-type": "application/json",
            "locale": "en_US",
            "origin": "https://jobs.apple.com",
            "referer": CAREERS_NAV_URL,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-apple-csrf-token": csrf_token,
        },
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("res", {})


def _format_url(position_id: str, transformed_title: str) -> str:
    # Apple's job-detail URL pattern: /en-us/details/{positionId}/{slug}
    return f"https://jobs.apple.com/en-us/details/{position_id}/{transformed_title}"


def fetch_apple_internships() -> list[dict]:
    """Convenience used by scrape.py: pull every active US Apple intern posting."""
    session = requests.Session()
    _prime_session(session)
    csrf = _get_csrf_token(session)

    jobs: list[dict] = []
    for page in range(1, 11):  # safety cap; ~44 results = ~3 pages typically
        page_data = _search_page(session, csrf, page=page)
        results = page_data.get("searchResults", []) or []
        if not results:
            break
        for r in results:
            jobs.append({
                "id": r.get("id") or r.get("positionId"),
                "title": r.get("postingTitle", ""),
                "url": _format_url(
                    r.get("positionId", ""),
                    r.get("transformedPostingTitle", ""),
                ),
            })
        if len(results) < PAGE_SIZE:
            break
    return jobs


if __name__ == "__main__":
    jobs = fetch_apple_internships()
    print(f"Found {len(jobs)} internships\n")
    for j in jobs[:15]:
        print(f"- {j['title']}")
        print(f"  {j['url']}")
