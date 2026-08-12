# Charak

Charak (CHANAKYA) is an AI-assisted healthcare navigation platform. It guides users toward relevant specialties and healthcare facilities from user-provided symptoms and documents. It is not a diagnostic, prescribing, or emergency-response service.

## Architecture

- **Frontend:** React, TypeScript, Vite, TanStack Start, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy, Pydantic Settings
- **AI:** Groq text and vision integrations, configured only by server-side environment variables
- **Hospital discovery:** verified database records plus OpenStreetMap/Overpass discovery
- **Database:** SQLite for local development; PostgreSQL required for Vercel production

```text
src/                 React/TanStack Start routes and UI
backend/app/         Existing FastAPI application, AI, database, and providers
api/index.py         Vercel entrypoint for the existing FastAPI app
vercel.json          Vercel function configuration
.env.example         Safe configuration template
```

## Local setup

```bash
git clone <repository-url>
cd charak-care-nav-main
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add your Groq key to `.env`; never commit that file.

Start the API:

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal at the repository root:

```bash
npm ci
npm run dev
```

With `VITE_API_BASE_URL` unset, the development frontend uses `http://127.0.0.1:8000`. Verify the API at `http://127.0.0.1:8000/health`.

## EC2 and Nginx deployment

For the EC2 deployment, leave `VITE_API_BASE_URL` unset or set it to `/api` in
the production build environment. Do not set it to a localhost, `127.0.0.1`,
or public `:8000` URL. The browser then requests `/api/health`, which Nginx
forwards to FastAPI's unprefixed `/health` route. The existing Nginx location
must retain its trailing slash:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
}
```

This keeps port 8000 private and does not require production browser CORS.

## Vercel deployment

The Vite configuration uses Nitro's Vercel preset, which creates Vercel Build Output for the existing TanStack Start frontend. It preserves direct frontend routes such as `/analyze`, `/hospitals`, and `/compare`. The existing FastAPI application is exposed by `api/index.py` under `/api/*`; no second FastAPI app or duplicate routers are created.

In **Vercel Project Settings → Environment Variables**, create the variables below for Preview and Production. For a single Vercel project, set `VITE_API_BASE_URL=/api`. Add your deployed domain to `CORS_ORIGINS`, for example `https://your-project.vercel.app`.

```bash
vercel login
vercel link
vercel
vercel --prod
```

Do not deploy with SQLite. Vercel's filesystem is ephemeral, so the backend intentionally rejects SQLite when `VERCEL` is set. Provision a persistent PostgreSQL database (such as Supabase or Neon), set its connection string as `DATABASE_URL`, and load only verified HFR/provider records through an explicit ingestion process. Charak does not seed hospitals, clinicians, pricing, or availability records.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Public API base URL; use `/api` for one Vercel project |
| `GROQ_API_KEY` | Server-only Groq access key |
| `GROQ_MODEL` | Groq text model identifier |
| `GROQ_VISION_MODEL` | Groq vision model identifier |
| `DATABASE_URL` | SQLAlchemy database URL; PostgreSQL on Vercel |
| `CORS_ORIGINS` | Comma-separated approved frontend origins |
| `LOCAL_HOSPITAL_PROVIDER` | Local discovery provider (`osm`) |
| `LOCAL_HOSPITAL_SEARCH_RADIUS_KM` | Default OSM radius in kilometres |
| `OSM_OVERPASS_URL` | Overpass endpoint |
| `OSM_DISCOVERY_CACHE_MINUTES` | OSM cache lifetime |
| `ADMIN_TOKEN` | Server-only token for `/api/admin/data-summary` |

Never place `GROQ_API_KEY`, `DATABASE_URL`, or `ADMIN_TOKEN` in a `VITE_*` variable.

## Validation

```bash
cd backend && pytest
cd ..
npx tsc --noEmit
npm run build
```

## Security and safety

- `.env` files, database files, virtual environments, and generated output are ignored by Git.
- Groq failures use the existing controlled safety fallback; no key is returned to the frontend.
- OSM requests have a timeout and return controlled empty/partial results on provider failure.
- Pricing and availability remain unavailable unless supplied by a verified provider.
- `GET /api/admin/data-summary` requires `X-Admin-Token` and never exposes the token.
- Charak provides healthcare navigation, not a medical diagnosis. Seek immediate professional emergency care for urgent symptoms.
