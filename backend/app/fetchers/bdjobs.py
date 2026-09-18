"""
Scrapes job listings from BDjobs.com — the largest job portal
in Bangladesh.

This is a best-effort scraper: BDjobs doesn't offer a public API,
so we parse their HTML search results. The scraper may need
updating if they change their page layout.

Category IDs used:
  8 = IT/Telecommunication
 14 = Engineering/Architect
"""

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://jobs.bdjobs.com"
SEARCH_URL = f"{BASE_URL}/jobsearch.asp"

# Categories to scrape — each costs one HTTP request.
CATEGORIES = [
    {"fcatId": "8", "label": "IT/Telecom"},
    {"fcatId": "14", "label": "Engineering"},
]

# Mimic a real browser to avoid being blocked.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_bdjobs(categories: list[dict] | None = None) -> list[dict]:
    """
    Scrape job listings from BDjobs.com for the configured categories.
    Returns a list of normalized job dicts.
    """
    categories = categories or CATEGORIES
    all_jobs: list[dict] = []
    seen: set[str] = set()  # title+company dedup key

    async with httpx.AsyncClient(
        timeout=20.0,
        headers=HEADERS,
        follow_redirects=True,
    ) as client:
        for cat in categories:
            try:
                resp = await client.get(
                    SEARCH_URL,
                    params={"fcatId": cat["fcatId"]},
                )
                resp.raise_for_status()
                jobs = _parse_listing_page(resp.text)
                print(f"[bdjobs] {cat['label']} (fcatId={cat['fcatId']}) → {len(jobs)} jobs")

                for job in jobs:
                    dedup_key = f"{job['title'].lower()}|{job['company'].lower()}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    all_jobs.append(job)

            except Exception as e:
                print(f"[bdjobs] Error scraping {cat['label']}: {e}")
                continue

    print(f"[bdjobs] Total unique jobs scraped: {len(all_jobs)}")
    return all_jobs


def _parse_listing_page(html: str) -> list[dict]:
    """
    Parse a BDjobs search results page and extract job listings.
    BDjobs uses a mix of table-based and div-based layouts. We try
    multiple selector strategies and take whichever yields results.
    """
    soup = BeautifulSoup(html, "lxml")
    jobs: list[dict] = []

    # ── Strategy 1: Look for job listing containers ──
    # BDjobs typically wraps each job in a div with class containing
    # 'job' or an anchor tag with the job URL pattern.
    job_links = soup.find_all("a", href=re.compile(r"jobdetails\.asp|job-detail", re.I))

    for link in job_links:
        try:
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = link.get("href", "")
            source_url = urljoin(BASE_URL, href) if href else ""

            # Walk up to the container to find company and other info.
            container = link.find_parent("div") or link.find_parent("tr")
            company = ""
            location = ""
            description = ""

            if container:
                # Look for company name — usually in a separate element
                # near the job title.
                text_elements = container.find_all(
                    ["span", "p", "div", "td", "a"],
                    string=re.compile(r".{3,}", re.DOTALL),
                )
                texts = [el.get_text(strip=True) for el in text_elements]
                texts = [t for t in texts if t and t != title]

                if texts:
                    company = texts[0]  # First non-title text is usually company
                if len(texts) > 1:
                    # Look for location-like text
                    for t in texts[1:]:
                        if any(loc in t.lower() for loc in [
                            "dhaka", "chittagong", "chattogram", "sylhet",
                            "rajshahi", "khulna", "barisal", "rangpur",
                            "comilla", "gazipur", "bangladesh", "remote",
                        ]):
                            location = t
                            break

                # Get full text of container as description
                full_text = container.get_text(" ", strip=True)
                if len(full_text) > len(title) + 20:
                    description = full_text[:1000]

            jobs.append({
                "title": _clean_text(title),
                "company": _clean_text(company) or "Company on BDjobs",
                "description": _clean_text(description),
                "location": _clean_text(location) or "Bangladesh",
                "source_url": source_url,
                "source": "bdjobs",
            })

        except Exception:
            continue

    # ── Strategy 2: Fallback — find structured data (JSON-LD) ──
    if not jobs:
        jobs = _parse_jsonld(soup)

    return jobs


def _parse_jsonld(soup: BeautifulSoup) -> list[dict]:
    """
    Some modern job pages embed Schema.org JobPosting data as JSON-LD.
    This gives us perfectly structured data when available.
    """
    import json

    jobs: list[dict] = []
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") != "JobPosting":
                    continue
                org = item.get("hiringOrganization", {})
                loc = item.get("jobLocation", {})
                address = loc.get("address", {}) if isinstance(loc, dict) else {}

                jobs.append({
                    "title": item.get("title", "").strip(),
                    "company": (
                        org.get("name", "") if isinstance(org, dict) else str(org)
                    ).strip() or "Unknown",
                    "description": item.get("description", "").strip()[:2000],
                    "location": address.get("addressLocality", "Bangladesh"),
                    "source_url": item.get("url", ""),
                    "source": "bdjobs",
                })
        except Exception:
            continue

    return jobs


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text
