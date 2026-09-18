from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import DEFAULT_MATCH_LIMIT
from app.database import get_db
from app.nlp.matcher import compute_match

router = APIRouter(prefix="/match", tags=["match"])


@router.get("/{profile_id}", response_model=list[schemas.MatchOut])
def get_matches(
    profile_id: int, limit: int = DEFAULT_MATCH_LIMIT, db: Session = Depends(get_db)
):
    profile = db.get(models.Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    jobs = db.query(models.Job).all()
    if not jobs:
        raise HTTPException(
            status_code=404,
            detail="No jobs in the database yet — call POST /jobs/seed first.",
        )

    results = []
    for job in jobs:
        result = compute_match(profile, job)
        results.append(
            schemas.MatchOut(
                job=schemas.JobOut.model_validate(job),
                overall_score=result.overall_score,
                breakdown=schemas.MatchBreakdown(**result.breakdown),
                matched_skills=result.matched_skills,
                missing_skills=result.missing_skills,
                explanation=result.explanation,
            )
        )

    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results[:limit]
