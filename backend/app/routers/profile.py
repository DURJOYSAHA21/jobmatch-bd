from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.nlp.cv_parser import parse_cv

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=schemas.ProfileOut)
def create_profile(payload: schemas.ProfileCreate, db: Session = Depends(get_db)):
    profile = models.Profile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=schemas.ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(models.Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=schemas.ProfileOut)
def update_profile(
    profile_id: int, payload: schemas.ProfileCreate, db: Session = Depends(get_db)
):
    profile = db.get(models.Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{profile_id}/cv", response_model=schemas.CVParseOut)
async def upload_cv(profile_id: int, file: UploadFile, db: Session = Depends(get_db)):
    """
    Parse an uploaded PDF CV and merge extracted skills/education into
    the profile. Returns what was found so the frontend can show the
    user what got auto-filled (and let them correct it).
    """
    profile = db.get(models.Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file")

    file_bytes = await file.read()
    parsed = parse_cv(file_bytes)

    existing_skills = {s.strip() for s in profile.skills.split(",") if s.strip()}
    merged_skills = sorted(existing_skills | set(parsed["skills"]))
    profile.skills = ", ".join(merged_skills)

    if not profile.education and parsed["education_guess"]:
        profile.education = parsed["education_guess"]

    db.commit()

    return schemas.CVParseOut(
        raw_text_preview=parsed["raw_text"][:500],
        skills=parsed["skills"],
        education_guess=parsed["education_guess"],
    )
