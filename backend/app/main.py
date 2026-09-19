import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import CORS_ORIGIN_REGEX, CORS_ORIGINS, CORS_ORIGINS_RAW
from app.database import Base, engine
from app.routers import jobs, match, profile, shortlist

logger = logging.getLogger("jobmatch")

app = FastAPI(
    title="JobMatch BD API",
    description="NLP-powered job discovery & matching for Bangladeshi job seekers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
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


def _preload_model():
    """
    Load the embedding model in the background once the server is up.

    Without this, the first person to open the Matches tab pays for importing
    torch/transformers AND loading the (80MB) model. Running it here — in a
    thread, so it never delays opening the port — means that cost is usually
    already paid by the time somebody clicks.
    """
    try:
        from app.nlp import embeddings

        embeddings.preload()
        logger.info("Embedding model preloaded and ready")
    except Exception:
        logger.warning("Model preload failed; will retry on first request")


@app.on_event("startup")
def on_startup():
    # Log the effective config: a wrong allowed-origin list is the most common
    # cause of "the frontend can't save anything", and the browser only reports
    # it as an opaque "Failed to fetch".
    print(f"[cors] raw            : {CORS_ORIGINS_RAW}")
    print(f"[cors] allowed origins: {CORS_ORIGINS}")
    print(f"[cors] origin regex   : {CORS_ORIGIN_REGEX or '(none)'}")

    try:
        _ensure_schema()
    except Exception:
        # A database hiccup must not stop the service from booting.
        logger.warning("Schema check failed; continuing", exc_info=True)

    # Daemon thread: returns immediately, so the port binds right away.
    threading.Thread(target=_preload_model, daemon=True).start()


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "jobmatch-bd-api",
        "cors_origins": CORS_ORIGINS,
        "cors_origin_regex": CORS_ORIGIN_REGEX,
    }
