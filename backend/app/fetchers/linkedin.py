"""
Scrapes public job listings from LinkedIn's guest API — no login or
API key required.

LinkedIn exposes a public endpoint for job search results that returns
HTML fragments with structured job cards. We parse these with
BeautifulSoup to extract job details.

This is the same data you see when browsing LinkedIn Jobs without
being logged in.
"""

import re
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

LINKEDIN_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)

# Search queries focused on tech/CS roles in Bangladesh.
SEARCH_QUERIES = [
    "software developer",
    "software engineer",
    "web developer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "python developer",
    "java developer",
    "data scientist",
    "machine learning",
    "DevOps engineer",
    "QA engineer",
    "mobile app developer",
    "UI UX designer",
    "database administrator",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_linkedin_jobs(
    queries: list[str] | None = None,
    location: str = "Bangladesh",
) -> list[dict]:
    """
    Scrape public LinkedIn job listings for the given queries.
    Returns a list of normalized job dicts ready for DB insertion.
    """
    queries = queries or SEARCH_QUERIES
    all_jobs: list[dict] = []
    seen_titles: set[str] = set()  # dedup key: lowercase title+company

    async with httpx.AsyncClient(
        timeout=20.0,
        headers=HEADERS,
        follow_redirects=True,
    ) as client:
        for query in queries:
            try:
                url = (
                    f"{LINKEDIN_URL}"
                    f"?keywords={quote_plus(query)}"
                    f"&location={quote_plus(location)}"
                    f"&start=0"
                )
                resp = await client.get(url)

                if resp.status_code == 429:
                    print(f"[linkedin] Rate limited — stopping after {len(all_jobs)} jobs.")
                    break

                if resp.status_code != 200:
                    print(f"[linkedin] HTTP {resp.status_code} for '{query}'")
                    continue

                jobs = _parse_linkedin_cards(resp.text)
                new_count = 0

                for job in jobs:
                    dedup_key = f"{job['title'].lower()}|{job['company'].lower()}"
                    if dedup_key in seen_titles:
                        continue
                    seen_titles.add(dedup_key)
                    all_jobs.append(job)
                    new_count += 1

                print(f"[linkedin] '{query}' → {len(jobs)} cards, {new_count} new")

            except Exception as e:
                print(f"[linkedin] Error fetching '{query}': {e}")
                continue

    print(f"[linkedin] Total unique jobs scraped: {len(all_jobs)}")
    return all_jobs


def _parse_linkedin_cards(html: str) -> list[dict]:
    """Parse LinkedIn job cards from the guest API HTML response."""
    soup = BeautifulSoup(html, "lxml")
    cards = soup.find_all("div", class_="base-card")
    jobs: list[dict] = []

    for card in cards:
        try:
            title_el = card.find("h3")
            company_el = card.find("h4")
            location_el = card.find("span", class_="job-search-card__location")
            link_el = card.find("a", class_="base-card__full-link")
            time_el = card.find("time")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            company = company_el.get_text(strip=True) if company_el else "Unknown"
            location = location_el.get_text(strip=True) if location_el else "Bangladesh"
            source_url = (link_el.get("href", "") if link_el else "").split("?")[0]

            # Build a description from available info
            description_parts = [title]
            if company:
                description_parts.append(f"Company: {company}")
            if location:
                description_parts.append(f"Location: {location}")

            # Try to get the listing date
            if time_el:
                date_text = time_el.get_text(strip=True)
                description_parts.append(f"Posted: {date_text}")

            # Look for any additional text/metadata in the card
            metadata_items = card.find_all(
                "span", class_=re.compile(r"job-search-card__", re.I)
            )
            for item in metadata_items:
                text = item.get_text(strip=True)
                if text and text not in [title, company, location] and len(text) > 2:
                    description_parts.append(text)

            jobs.append({
                "title": _clean(title),
                "company": _clean(company),
                "description": " · ".join(description_parts),
                "location": _clean(location),
                "source_url": source_url,
                "source": "linkedin",
            })

        except Exception:
            continue

    return jobs


def _clean(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()
