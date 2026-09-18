"""Test scraping LinkedIn public job listings (no auth needed)."""
import httpx
from bs4 import BeautifulSoup

QUERIES = [
    "software developer",
    "web developer",
    "data scientist",
    "machine learning",
    "python developer",
]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

total = 0
for q in QUERIES:
    url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={q.replace(' ', '+')}&location=Bangladesh&start=0"
    )
    try:
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        print(f"\n[{q}] Status: {r.status_code}, Length: {len(r.text)}")

        if r.status_code == 200 and len(r.text) > 100:
            soup = BeautifulSoup(r.text, "lxml")
            cards = soup.find_all("div", class_="base-card")
            print(f"  Cards found: {len(cards)}")
            total += len(cards)

            for c in cards[:3]:
                title = c.find("h3")
                company = c.find("h4")
                location = c.find("span", class_="job-search-card__location")
                link = c.find("a", class_="base-card__full-link")

                t = title.get_text(strip=True) if title else "?"
                co = company.get_text(strip=True) if company else "?"
                loc = location.get_text(strip=True) if location else "?"
                href = link.get("href", "") if link else ""

                print(f"  - {t} @ {co} ({loc})")
        else:
            print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal jobs found across all queries: {total}")
