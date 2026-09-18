import os

from dotenv import load_dotenv

load_dotenv()

# Local dev default: SQLite file, zero setup required.
# For deployment, set DATABASE_URL to a Postgres connection string
# (e.g. from Neon or Supabase) — see README "Deployment" section.
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./jobmatch.db"

# Comma-separated list of allowed frontend origins for CORS.
# In dev this defaults to the Vite dev server port.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

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
