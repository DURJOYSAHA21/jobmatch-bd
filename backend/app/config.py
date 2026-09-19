import os
import re

from dotenv import load_dotenv

load_dotenv()

# Local dev default: SQLite file, zero setup required.
# For deployment, set DATABASE_URL to a Postgres connection string
# (e.g. from Neon or Supabase) — see README "Deployment" section.
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./jobmatch.db"


# ── CORS ──────────────────────────────────────────────────────────────────
#
# Split CORS_ORIGINS on commas into exact origins and wildcard patterns.
# A "*" is allowed inside an entry, e.g. "https://*.vercel.app", so Vercel
# preview deployments (which get a new hostname per deploy) don't break the
# production app.
#
# Gotchas this handles, all of which look like "the API is broken" from the
# browser (the request fails the preflight with 400 "Disallowed CORS origin"
# and the frontend only sees a bare "Failed to fetch"):
#   - a trailing slash in the configured URL ("https://x.vercel.app/")
#   - whitespace around commas
#   - the Vite dev server falling back to 5174 when 5173 is taken
#
DEFAULT_CORS_ORIGINS = ",".join(
    [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://*.vercel.app",
    ]
)


def _parse_cors_origins(raw: str) -> tuple[list[str], str | None]:
    """
    Return (exact_origins, origin_regex).

    Entries without "*" are passed to CORSMiddleware.allow_origins verbatim.
    Entries containing "*" are compiled into a single regex for
    CORSMiddleware.allow_origin_regex.
    """
    entries = [o.strip().rstrip("/") for o in (raw or "").split(",")]
    entries = [o for o in entries if o]

    exact: list[str] = []
    patterns: list[str] = []
    for origin in entries:
        if origin == "*":
            # Plain "*" — allow everything. Starlette handles this itself.
            exact.append("*")
        elif "*" in origin:
            patterns.append(origin)
        else:
            exact.append(origin)

    regex = None
    if patterns:
        # re.escape the literal parts, then let "*" become ".*"
        escaped = [re.escape(p).replace(r"\*", ".*") for p in patterns]
        regex = "^(?:" + "|".join(escaped) + ")$"

    return exact, regex


CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS") or DEFAULT_CORS_ORIGINS
CORS_ORIGINS, CORS_ORIGIN_REGEX = _parse_cors_origins(CORS_ORIGINS_RAW)

# How many ranked matches to return per profile by default.
DEFAULT_MATCH_LIMIT = int(os.getenv("DEFAULT_MATCH_LIMIT", "20"))

# RapidAPI key for JSearch job fetching.
# Sign up free at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# Email alerts when new jobs match a profile (SMTP).
# Leave SMTP_HOST empty to disable sending (emails are skipped quietly).
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

# Minimum overall match score (0-100) required to trigger an email alert.
MATCH_EMAIL_THRESHOLD = float(os.getenv("MATCH_EMAIL_THRESHOLD", "50"))
