"""
Orchestrates job fetching from all configured sources and inserts
new, unique jobs into the database.

Sources:
  - linkedin : Scrapes LinkedIn public job listings (no API key needed)
  - jsearch  : JSearch API via RapidAPI (needs RAPIDAPI_KEY)
  - bdjobs   : BDjobs.com scraper (best-effort HTML parsing)

Usage from the API:
    POST /jobs/fetch              — fetches from all sources
    POST /jobs/fetch?source=linkedin  — LinkedIn only
    POST /jobs/fetch?source=jsearch   — JSearch only
"""

from sqlalchemy.orm import Session

from app import models
from app.fetchers.linkedin import fetch_linkedin_jobs
from app.notifications.alerts import notify_profiles_of_new_jobs

VALID_SOURCES = {"linkedin", "jsearch", "bdjobs"}


async def fetch_and_store(
    db: Session,
    source: str | None = None,
) -> dict:
    """
    Fetch jobs from the requested source(s), deduplicate against what's
    already in the database, and insert new listings.

    Returns a summary dict with per-source stats.
    """
    results: dict[str, dict] = {}
    raw_jobs: list[dict] = []

    # ── LinkedIn (primary — no API key needed) ──
    if source in (None, "linkedin"):
        try:
            linkedin_jobs = await fetch_linkedin_jobs()
            results["linkedin"] = {"fetched": len(linkedin_jobs), "new": 0, "skipped": 0}
            raw_jobs.extend(linkedin_jobs)
        except Exception as e:
            print(f"[manager] LinkedIn error: {e}")
            results["linkedin"] = {"fetched": 0, "new": 0, "skipped": 0, "error": str(e)}

    # ── JSearch API (needs RAPIDAPI_KEY) ──
    if source in (None, "jsearch"):
        try:
            from app.fetchers.jsearch import fetch_jsearch_jobs
            jsearch_jobs = await fetch_jsearch_jobs()
            results["jsearch"] = {"fetched": len(jsearch_jobs), "new": 0, "skipped": 0}
            raw_jobs.extend(jsearch_jobs)
        except Exception as e:
            print(f"[manager] JSearch error: {e}")
            results["jsearch"] = {"fetched": 0, "new": 0, "skipped": 0, "error": str(e)}

    # ── BDjobs scraper ──
    if source == "bdjobs":
        try:
            from app.fetchers.bdjobs import fetch_bdjobs
            bdjobs_jobs = await fetch_bdjobs()
            results["bdjobs"] = {"fetched": len(bdjobs_jobs), "new": 0, "skipped": 0}
            raw_jobs.extend(bdjobs_jobs)
        except Exception as e:
            print(f"[manager] BDjobs error: {e}")
            results["bdjobs"] = {"fetched": 0, "new": 0, "skipped": 0, "error": str(e)}

    if not raw_jobs:
        return {"status": "no_results", "sources": results}

    # ── Deduplicate against existing DB jobs ──
    existing_jobs = db.query(models.Job.title, models.Job.company).all()
    existing_keys: set[str] = set()
    for title, company in existing_jobs:
        existing_keys.add(_dedup_key(title, company))

    # ── Insert new jobs ──
    inserted_jobs: list[models.Job] = []
    for job in raw_jobs:
        key = _dedup_key(job["title"], job["company"])
        source_name = job.pop("source", "unknown")

        if key in existing_keys:
            if source_name in results:
                results[source_name]["skipped"] += 1
            continue

        existing_keys.add(key)

        db_job = models.Job(
            title=job["title"],
            company=job["company"],
            description=job.get("description", "")[:5000],
            location=job.get("location", "Bangladesh"),
            source_url=job.get("source_url", ""),
        )
        db.add(db_job)
        inserted_jobs.append(db_job)

        if source_name in results:
            results[source_name]["new"] += 1

    notifications = {"emails_sent": 0, "profiles_checked": 0}
    if inserted_jobs:
        db.commit()
        for job in inserted_jobs:
            db.refresh(job)
        try:
            notifications = notify_profiles_of_new_jobs(db, inserted_jobs)
        except Exception as e:
            print(f"[manager] Notification error: {e}")

    total_in_db = db.query(models.Job).count()

    return {
        "status": "ok",
        "new_jobs_added": len(inserted_jobs),
        "total_jobs_in_db": total_in_db,
        "sources": results,
        "notifications": notifications,
    }


def _dedup_key(title: str, company: str) -> str:
    return f"{title.strip().lower()}|{company.strip().lower()}"
