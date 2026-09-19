import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import DEFAULT_MATCH_LIMIT
from app.database import get_db
from app.nlp import embeddings
from app.nlp.matcher import compute_match, profile_full_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["match"])


# NOTE: this route is declared before /{profile_id} on purpose. FastAPI
# matches routes in declaration order, and "debug" would otherwise be parsed
# as a profile_id (and rejected as an invalid integer).
@router.get("/debug/self-check")
def self_check(db: Session = Depends(get_db)):
    """
    Diagnostics for "the Matches page is broken".

    Reports counts, embedding-cache state, and — most importantly — the actual
    traceback if the embedding model can't be loaded. A model load failure
    normally only shows up as a 500 with no detail in the browser, so this
    endpoint exists so the reason is reachable with a plain URL:

        /match/debug/self-check
    """
    info: dict = {
        "jobs": db.query(models.Job).count(),
        "profiles": db.query(models.Profile).count(),
        "cache": embeddings.cache_stats(),
    }

    try:
        vector = embeddings.embed("self check")
        info["model"] = "ok"
        info["vector_size"] = int(len(vector))
        info["model_error"] = None
    except Exception:
        info["model"] = "FAILED"
        info["model_error"] = traceback.format_exc()

    return info


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

    # Encode every job description in ONE batched call before scoring.
    # Without this, scoring N jobs costs N separate model encodes, which is
    # both very slow and memory-hungry. If it fails, keep going — scoring
    # falls back to a neutral semantic score (see matcher.score_semantic)
    # rather than failing the whole page.
    try:
        embeddings.warm_cache(
            [profile_full_text(profile)] + [job.description or "" for job in jobs]
        )
    except Exception:
        logger.warning("Embedding warm-up failed; continuing without it", exc_info=True)

    results = []
    failures = 0
    first_error = ""

    for job in jobs:
        try:
            result = compute_match(profile, job)
        except Exception:
            # One malformed posting must not take down the whole page.
            failures += 1
            if not first_error:
                first_error = traceback.format_exc()
            logger.warning("Scoring failed for job %s", job.id, exc_info=True)
            continue

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

    if not results:
        # Every single job failed — something systemic. Say so plainly instead
        # of returning an empty list the UI would render as "No matches found".
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not score any of the {len(jobs)} jobs in the database. "
                f"First error:\n{first_error[-800:]}"
            ),
        )

    if failures:
        logger.warning("Scored %s jobs, skipped %s", len(results), failures)

    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results[:limit]
