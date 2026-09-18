"""
Fetches jobs from the JSearch API (RapidAPI) — aggregates from
Google Jobs, LinkedIn, Indeed, Glassdoor, etc.

Free tier: 200 requests/month. Each request returns up to 10 jobs.
We run a handful of tech-focused queries filtered to Bangladesh.

Sign up: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""

import httpx

from app.config import RAPIDAPI_KEY

JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_URL = f"https://{JSEARCH_HOST}/search"

# Queries to rotate through — focused on tech/CS roles in Bangladesh.
# Each query costs 1 API request. With 200 free/month, we can afford
# to run ~12 queries a few times a week.
SEARCH_QUERIES = [
    "software developer in Bangladesh",
    "web developer in Bangladesh",
    "data scientist in Bangladesh",
    "machine learning engineer in Bangladesh",
    "backend developer in Bangladesh",
    "frontend developer in Bangladesh",
    "full stack developer in Bangladesh",
    "DevOps engineer in Bangladesh",
    "Python developer in Bangladesh",
    "Java developer in Bangladesh",
    "software engineer Dhaka",
    "IT jobs Dhaka Bangladesh",
]


async def fetch_jsearch_jobs(
    queries: list[str] | None = None,
    num_pages: int = 1,
) -> list[dict]:
    """
    Fetch jobs from JSearch API for the given queries.
    Returns a list of normalized job dicts ready for DB insertion.
    """
    if not RAPIDAPI_KEY:
        print("[jsearch] No RAPIDAPI_KEY configured — skipping JSearch.")
        return []

    queries = queries or SEARCH_QUERIES
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }

    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            try:
                resp = await client.get(
                    JSEARCH_URL,
                    headers=headers,
                    params={
                        "query": query,
                        "page": "1",
                        "num_pages": str(num_pages),
                        "country": "bd",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("data", []) or []:
                    job_id = item.get("job_id", "")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = (item.get("job_title") or "").strip()
                    company = (item.get("employer_name") or "").strip()
                    if not title:
                        continue

                    all_jobs.append({
                        "title": title,
                        "company": company or "Unknown",
                        "description": (item.get("job_description") or "").strip(),
                        "location": _build_location(item),
                        "source_url": item.get("job_apply_link") or "",
                        "source": "jsearch",
                    })

                print(f"[jsearch] '{query}' → {len(data.get('data', []) or [])} results")

            except httpx.HTTPStatusError as e:
                print(f"[jsearch] HTTP {e.response.status_code} for '{query}': {e}")
                if e.response.status_code == 429:
                    print("[jsearch] Rate limited — stopping further queries.")
                    break
            except Exception as e:
                print(f"[jsearch] Error fetching '{query}': {e}")
                continue

    print(f"[jsearch] Total unique jobs fetched: {len(all_jobs)}")
    return all_jobs


def _build_location(item: dict) -> str:
    city = (item.get("job_city") or "").strip()
    state = (item.get("job_state") or "").strip()
    country = (item.get("job_country") or "").strip()
    parts = [p for p in [city, state] if p]
    loc = ", ".join(parts)
    if not loc:
        loc = country if country else "Bangladesh"
    return loc
