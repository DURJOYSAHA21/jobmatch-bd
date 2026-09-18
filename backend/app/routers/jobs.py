import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.fetchers.manager import fetch_and_store

router = APIRouter(prefix="/jobs", tags=["jobs"])

SEED_CSV_PATH = Path(__file__).resolve().parent.parent / "seed_data" / "jobs_seed.csv"


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    return (
        db.query(models.Job)
        .order_by(models.Job.created_at.desc())
        .offset(skip)
        .limit(min(limit, 1000))
        .all()
    )


@router.get("/count")
def job_count(db: Session = Depends(get_db)):
    """Quick endpoint to check how many jobs are in the database."""
    count = db.query(models.Job).count()
    return {"count": count}


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/seed")
def seed_jobs(db: Session = Depends(get_db)):
    """
    Dev/demo utility: loads the sample postings in seed_data/jobs_seed.csv
    into the database. These are hand-written sample postings for
    development — NOT scraped data. Swap this out for a real, permitted
    source before treating this as production data (see README "Data
    sources" section).
    """
    if db.query(models.Job).count() > 0:
        return {"status": "skipped", "reason": "jobs table already has data"}

    if not SEED_CSV_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Seed file not found: {SEED_CSV_PATH}")

    count = 0
    seeded: list[models.Job] = []
    with open(SEED_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job = models.Job(
                title=row["title"],
                company=row["company"],
                description=row["description"],
                location=row["location"],
                source_url=row.get("source_url", ""),
            )
            db.add(job)
            seeded.append(job)
            count += 1
    db.commit()
    for job in seeded:
        db.refresh(job)

    notifications = {"emails_sent": 0, "profiles_checked": 0}
    try:
        from app.notifications.alerts import notify_profiles_of_new_jobs
        notifications = notify_profiles_of_new_jobs(db, seeded)
    except Exception as e:
        print(f"[seed] Notification error: {e}")

    return {
        "status": "seeded",
        "jobs_added": count,
        "notifications": notifications,
    }


@router.post("/fetch")
async def fetch_jobs(
    source: str | None = Query(
        None,
        description="Which source to fetch from: 'jsearch', 'bdjobs', or omit for all.",
    ),
    db: Session = Depends(get_db),
):
    """
    Fetch real job listings from the internet.

    Sources:
    - **jsearch** — JSearch API (RapidAPI) aggregating Google Jobs,
      LinkedIn, Indeed. Requires RAPIDAPI_KEY env var.
    - **bdjobs** — Scrapes BDjobs.com (best-effort, may need updating
      if they change their HTML layout).
    - **omit** — Fetch from all sources.

    Deduplicates against existing jobs in the database by title + company.
    """
    if source and source not in ("linkedin", "jsearch", "bdjobs"):
        raise HTTPException(
            status_code=400,
            detail="source must be 'linkedin', 'jsearch', 'bdjobs', or omitted for all.",
        )

    result = await fetch_and_store(db, source=source)
    return result


@router.delete("/clear")
def clear_jobs(db: Session = Depends(get_db)):
    """
    Dev utility: removes all jobs from the database.
    Useful for re-fetching fresh data.
    """
    count = db.query(models.Job).count()
    db.query(models.Shortlist).delete()
    db.query(models.Job).delete()
    db.commit()
    return {"status": "cleared", "jobs_removed": count}
