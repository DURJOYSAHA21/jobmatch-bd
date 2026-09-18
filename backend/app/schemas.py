from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Profile ----------

class ProfileCreate(BaseModel):
    name: str = ""
    email: str = ""
    education: str = ""
    skills: str = ""       # "Python, C#, ASP.NET Core, SQL, Machine Learning"
    interests: str = ""
    experience: str = ""
    location: str = ""


class ProfileOut(ProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CVParseOut(BaseModel):
    raw_text_preview: str
    skills: list[str]
    education_guess: str | None


# ---------- Job ----------

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    description: str
    location: str
    source_url: str
    created_at: datetime


# ---------- Match ----------

class MatchBreakdown(BaseModel):
    semantic_similarity: float
    skill_overlap: float
    education_match: float
    experience_match: float
    location_match: float


class MatchOut(BaseModel):
    job: JobOut
    overall_score: float
    breakdown: MatchBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str


# ---------- Shortlist ----------

class ShortlistCreate(BaseModel):
    profile_id: int
    job_id: int
    status: str = "shortlisted"  # saved | shortlisted | not_interested


class ShortlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job: JobOut
    status: str
    created_at: datetime
