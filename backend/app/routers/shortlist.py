from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/shortlist", tags=["shortlist"])

_VALID_STATUSES = {"saved", "shortlisted", "not_interested"}


@router.post("", response_model=schemas.ShortlistOut)
def upsert_shortlist_entry(payload: schemas.ShortlistCreate, db: Session = Depends(get_db)):
    if payload.status not in _VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {_VALID_STATUSES}")

    if not db.get(models.Profile, payload.profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    if not db.get(models.Job, payload.job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    entry = (
        db.query(models.Shortlist)
        .filter_by(profile_id=payload.profile_id, job_id=payload.job_id)
        .first()
    )
    if entry:
        entry.status = payload.status
    else:
        entry = models.Shortlist(**payload.model_dump())
        db.add(entry)

    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{profile_id}", response_model=list[schemas.ShortlistOut])
def list_shortlist(profile_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Shortlist)
        .filter_by(profile_id=profile_id)
        .order_by(models.Shortlist.created_at.desc())
        .all()
    )
