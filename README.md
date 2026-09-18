# JobMatch BD

NLP-powered job discovery and matching for Bangladeshi CS/software job seekers.
A user builds a profile (or uploads a CV), and the system ranks open postings
against it using a mix of semantic (embedding-based) similarity and structured
skill/education/experience/location matching — with a plain-English
explanation for every score, not just a bare percentage.

This is the MVP scope described in the original project plan: one category
(tech/CS jobs), one safe data source (hand-written sample postings for now),
and the core loop — profile → ranked matches → shortlist.

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   React     │────▶│   FastAPI    │────▶│   Postgres/    │
│  frontend   │◀────│   backend    │◀────│   SQLite       │
└─────────────┘     └──────┬───────┘     └───────────────┘
                            │
                    ┌───────┴────────┐
                    │  NLP core      │
                    │  - skill       │
                    │    extraction  │
                    │  - embeddings  │
                    │  - match       │
                    │    scoring     │
                    └────────────────┘
```

## Repo structure

```
backend/
  app/
    main.py              FastAPI app, CORS, router wiring
    config.py             env var loading
    database.py            SQLAlchemy engine/session
    models.py               Job, Profile, Shortlist tables
    schemas.py                Pydantic request/response models
    routers/
      profile.py               create/update profile, CV upload
      jobs.py                    list jobs, seed sample data
      match.py                     ranked matches for a profile
      shortlist.py                   save/shortlist jobs
    nlp/
      skills_taxonomy.py            canonical skills + aliases
      extractor.py                    PhraseMatcher-based skill extraction
      embeddings.py                     sentence-transformers wrapper
      matcher.py                          scoring + explanation engine
      cv_parser.py                         PDF text extraction
    seed_data/jobs_seed.csv                 16 sample postings (hand-written)
  requirements.txt
  .env.example
frontend/
  src/
    App.jsx                onboarding + profile rail + tabs
    api.js                   backend client
    components/
      ProfileForm.jsx           profile fields + CV upload
      JobFeed.jsx                  fetches + renders ranked matches
      JobCard.jsx                    score, skill tags, explanation
      Shortlist.jsx                    saved jobs view
  package.json
  .env.example
```

## Local setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # defaults are fine for local dev
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).
On first run it creates a local `jobmatch.db` SQLite file automatically —
no database setup needed for local dev.

The **first** call that touches matching will take a few seconds while it
downloads the `all-MiniLM-L6-v2` embedding model (~80MB, one-time, cached
after that).

Load the sample postings once the server is running:

```bash
curl -X POST http://localhost:8000/jobs/seed
```

(Or just click "Load sample jobs" in the frontend — it calls the same endpoint.)

### Frontend

```bash
cd frontend
npm install
cp .env.example .env          # points at localhost:8000 by default
npm run dev
```

Open `http://localhost:5173`, fill in the profile form (or use the CV
upload), and you'll see ranked matches against the sample postings.

## How matching works

Each (profile, job) pair gets scored on five signals, weighted and summed
(see `app/nlp/matcher.py` for exact weights):

- **Semantic similarity** — embedding similarity between your whole profile
  and the job description. This is what catches a match like your profile
  saying "machine learning, NLP, deep learning" against a posting that says
  "developing intelligent systems using neural networks and language
  models" — no shared keywords, but the same underlying meaning.
- **Skill overlap** — structured comparison of skills extracted from your
  profile vs. skills extracted from the posting, using a curated taxonomy
  (`skills_taxonomy.py`). This catches the literal, precise requirements
  the semantic score can be fuzzy about.
- **Education, experience, location** — simpler heuristic checks (see
  docstrings in `matcher.py`); intentionally straightforward for the MVP
  and easy to extend once you have more data to tune against.

The explanation you see under each job ("Strong match on Python, SQL...
The posting also asks for Docker...") is generated from the same matched/
missing skill sets, not a separate LLM call — deterministic and free to run.

## Data sources

The seed data (`seed_data/jobs_seed.csv`) is a set of hand-written sample
postings for development and demoing — not scraped from any real site, so
there's no terms-of-service question with it. For real production job data:

- Check whether BDjobs (or another board) offers a permitted feed/API, or
  request permission directly — their ToS places conditions around reuse
  of posted data.
- Alternatively, start with a licensed/public job-postings dataset, or
  manually curate postings, while you sort out a permitted live source.
- The architecture keeps ingestion separate from matching for exactly this
  reason — swap `POST /jobs/seed` for a real ingestion job later without
  touching the NLP core at all.

## Deployment

Step-by-step production guide: **[DEPLOY.md](DEPLOY.md)** (Neon Postgres + Render API + Vercel frontend).

Short version:

1. **Database** — create a free Postgres instance on
   [Neon](https://neon.tech) or [Supabase](https://supabase.com). Copy the
   connection string.
2. **Backend** — push this repo to GitHub, then deploy `backend/` on
   [Render](https://render.com) or [Railway](https://railway.app) as a
   Python web service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Env vars: `DATABASE_URL` (from step 1), `CORS_ORIGINS` (your Vercel
     URL, added after step 3 — redeploy once you have it)
3. **Frontend** — deploy `frontend/` on [Vercel](https://vercel.com):
   - Framework preset: Vite
   - Env var: `VITE_API_URL` = your Render/Railway backend URL
4. Hit `POST /jobs/seed` on the deployed backend once to load sample data
   (or point your ingestion pipeline at it once you have a real source).

## Known limitations / next steps

These are deliberate MVP simplifications, called out so you know what
you're extending rather than debugging:

- **Embeddings are computed per request, not cached.** Fine for a few
  dozen jobs; before scaling up, precompute and store job embeddings at
  ingestion time instead of re-encoding every job on every match request.
- **Education/experience scoring are keyword heuristics**, not structured
  parsing — documented in `matcher.py`, easy to replace once you have
  labeled data to justify something fancier.
- **The skills taxonomy is a starting list (~55 skills)** focused on
  tech/CS roles — extend `skills_taxonomy.py` as you add job categories.
- **CORS defaults to permissive in dev** — make sure `CORS_ORIGINS` is set
  to your actual deployed frontend URL in production, not `*`.
- Skill-gap analytics, saved searches, and the internships/scholarships/
  hackathons expansion mentioned in the original plan are all natural v2
  additions once this core loop is solid.
