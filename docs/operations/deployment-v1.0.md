# Deployment Guide v1.0 — Vercel (frontend) + Render (backend)

DAMGA-OPS is split into a static React frontend and a FastAPI backend. They deploy
to two different platforms and are wired together with one environment variable.

```
Browser ──▶ Vercel (apps/frontend, static)
               │  fetch(`${VITE_API_BASE_URL}/api/v1/...`)
               ▼
            Render (Dockerfile, FastAPI + SQLite)
```

> Data note: the backend runs on synthetic data only. On boot it applies Alembic
> migrations and re-seeds the Golden Dataset (`scripts/seed.py`, idempotent by
> file SHA-256). On Render's free tier the disk is ephemeral, so operator-entered
> data (shadow imports, decision actions) resets on each redeploy. That is
> acceptable for this prototype; see "Persisting data" below to change it.

---

## 1. Backend → Render

### Files in the repo
| File | Purpose |
|---|---|
| `Dockerfile` | `python:3.14-slim`, installs `requirements.txt`, runs `docker-entrypoint.sh` |
| `docker-entrypoint.sh` | `alembic upgrade head` → `python scripts/seed.py` → `uvicorn ... --port $PORT` |
| `render.yaml` | Render Blueprint (web service, Docker runtime, `/health` check) |
| `.dockerignore` | keeps the frontend and local DB out of the image |

### Steps
1. Push this repo to GitHub (done).
2. Render dashboard → **New → Blueprint** → select the repo. It reads `render.yaml`
   and creates the `damga-ops-api` web service.
   - Or **New → Web Service**, pick "Docker", leave build/start blank (the
     Dockerfile's `CMD` handles start).
3. Wait for the first deploy. Health check: `https://<service>.onrender.com/health`
   should return `{"status":"ok","service":"DAMGA-OPS API","version":"6.0.0-prototype"}`.
4. Smoke test:
   `GET https://<service>.onrender.com/api/v1/dashboard/daily?business_date=2026-08-31`
5. Copy the service URL — it becomes `VITE_API_BASE_URL` below.

### Notes
- CORS is already `allow_origins=["*"]`, so the Vercel origin can call it directly.
- Free instances sleep after ~15 min idle; the first request after that takes
  ~30–50 s to wake.

---

## 2. Frontend → Vercel

### Files in the repo
| File | Purpose |
|---|---|
| `apps/frontend/vercel.json` | framework=vite, build/output config, SPA rewrite (excludes `/api`) |
| `apps/frontend/.env.example` | documents `VITE_API_BASE_URL` |
| `apps/frontend/src/api/client.ts` | prefixes every request with `import.meta.env.VITE_API_BASE_URL` |

### Steps
1. Vercel dashboard → **Add New → Project** → import the repo.
2. Set **Root Directory = `apps/frontend`**. The framework preset (Vite),
   build command (`npm run build`) and output (`dist`) come from `vercel.json`.
3. **Environment Variables** → add:
   ```
   VITE_API_BASE_URL = https://<your-render-service>.onrender.com
   ```
   (no trailing slash; `client.ts` strips one anyway). Apply to Production
   (and Preview if you want preview deploys to hit the same backend).
4. Deploy. Open the Vercel URL — the cockpit should load today's sales, the six
   tabs, trends, and the bottom AI section.

### Local dev is unchanged
`VITE_API_BASE_URL` unset → `client.ts` calls `/api/v1/...` → the Vite dev proxy
(`vite.config.ts`) forwards to `http://127.0.0.1:8000`.

---

## 3. Verifying the pair

1. Vercel URL loads without console errors.
2. Network tab shows requests going to `https://<render>.onrender.com/api/v1/...`
   with `200`.
3. Change the date with the header arrows — KPIs and alerts update.
4. `2026-08-21` shows the `DATA_INCOMPLETE` banner and blocked AI section
   (proves the deterministic gate is live end-to-end).

---

## 4. Persisting data (optional, beyond the prototype)

The ephemeral SQLite is fine for a synthetic demo. To keep operator-entered data:

- **Render Disk**: add a disk mounted at `/app/data` (1 GB free tier). The SQLite
  file then survives redeploys. Seed still re-runs but is idempotent.
- **Managed Postgres**: provision Postgres (Render / Neon / Supabase), set
  `DATABASE_URL` env var on the service. `apps/api/database.py` already switches
  `connect_args` by URL scheme; `alembic.ini`'s `sqlalchemy.url` would also need
  to point at the same DB (or override it in `migrations/env.py` from the env var).

---

## 5. CI check before deploy

```powershell
.\bootstrap.ps1        # venv, deps, alembic upgrade, pytest, vitest, build
```
All green = safe to deploy. Current baseline: pytest 202, vitest 25,
playwright 18, build PASS.
