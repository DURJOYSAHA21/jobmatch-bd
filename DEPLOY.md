# Deploy JobMatch BD (Neon + Render + Vercel)

Follow these steps in order. Secrets stay in each host's dashboard — never commit `.env`.

## Prerequisites

- GitHub account (repo for this project)
- Free accounts: [Neon](https://neon.tech), [Render](https://render.com), [Vercel](https://vercel.com)

---

## 1. Database — Neon

1. Create a project at https://console.neon.tech
2. Copy the connection string (use the **pooled** URL if Neon shows one), e.g.  
   `postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`
3. Keep it for Render's `DATABASE_URL`.

Tables are created automatically on backend startup.

---

## 2. Backend — Render

1. New → **Web Service** → connect the GitHub repo
2. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment variables:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Neon connection string |
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app` (set after Vercel deploy, then redeploy) |
| `RAPIDAPI_KEY` | Optional — for live JSearch fetch |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | Optional — email alerts |

4. Deploy. Open `https://YOUR-SERVICE.onrender.com/` — expect `{"status":"ok","service":"jobmatch-bd-api"}`.
5. Seed sample jobs once:

```bash
curl -X POST https://YOUR-SERVICE.onrender.com/jobs/seed
```

**Note:** Free Render spins down after idle; first request (and first match) can take 30–60s while the MiniLM model downloads.

Alternatively apply the repo root [`render.yaml`](render.yaml) Blueprint and fill in the synced env vars.

---

## 3. Frontend — Vercel

1. Import the same GitHub repo at https://vercel.com/new
2. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
3. Environment variable:

| Key | Value |
|-----|--------|
| `VITE_API_URL` | `https://YOUR-SERVICE.onrender.com` (no trailing slash) |

4. Deploy. Copy the production URL (e.g. `https://jobmatch-bd.vercel.app`).
5. Back on Render: set `CORS_ORIGINS` to that exact origin (include `https://`), then **Manual Deploy**.

---

## 4. Verify

1. Open the Vercel URL
2. Create a profile (add email if you want alerts)
3. Load sample jobs or Fetch jobs
4. Check **Matches**, **All Jobs**, and **Shortlist**

If the browser shows CORS errors, `CORS_ORIGINS` on Render must match the Vercel origin exactly.

---

## Env cheat sheet

**Render (backend):** `DATABASE_URL`, `CORS_ORIGINS`, optional `RAPIDAPI_KEY`, optional SMTP_*  

**Vercel (frontend):** `VITE_API_URL`
