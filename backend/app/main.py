from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import jobs, match, profile, shortlist

app = FastAPI(
    title="JobMatch BD API",
    description="NLP-powered job discovery & matching for Bangladeshi job seekers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(match.router)
app.include_router(shortlist.router)


def _ensure_schema():
    """create_all won't add new columns to existing tables — patch those here."""
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if "profiles" not in insp.get_table_names():
        return
    columns = {col["name"] for col in insp.get_columns("profiles")}
    if "email" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE profiles ADD COLUMN email VARCHAR(255) DEFAULT ''")
            )


@app.on_event("startup")
def on_startup():
    _ensure_schema()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "jobmatch-bd-api"}
