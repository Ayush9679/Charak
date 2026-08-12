# Charak

Charak is an AI-assisted healthcare navigation platform. It interprets user-provided symptoms and documents to suggest an appropriate care specialty and urgency category, then helps users discover suitable nearby healthcare facilities. It is not a diagnostic or emergency-response service.

## Features

- Symptom and document-informed, safety-focused care navigation
- Deterministic triage fallback when the LLM is unavailable
- Hospital discovery, comparison, proximity, and specialty matching
- Currado conversational healthcare navigation assistant
- FastAPI health check at `GET /health`

## Technology stack

- Frontend: React 19, TypeScript, Vite, TanStack Start, Tailwind CSS
- Backend: Python 3.13, FastAPI, SQLAlchemy, Pydantic Settings
- AI: Groq-compatible chat and vision API (optional locally; configured by `GROQ_API_KEY`)
- Data: SQLite by default

## Project structure

```text
.
├── src/                    # React/TanStack frontend
├── public/                 # Static frontend assets
├── backend/
│   ├── app/                # FastAPI application
│   ├── tests/              # Backend test suite
│   ├── requirements.txt    # Pinned Python dependencies
│   └── Dockerfile          # Backend production container
├── .env.example            # Safe configuration template
├── .gitignore
├── package.json
└── README.md
```

## Prerequisites

- Node.js 20+ and npm
- Python 3.13+ (Python 3.11+ may also work)
- A Groq API key to enable LLM and vision responses in production

## Installation and local execution

Clone and enter the repository:

```bash
git clone <repository-url>
cd charak-care-nav-main
```

Create your local configuration from the safe template:

```bash
cp .env.example .env
```

Windows PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` in `.env` to your real key. Never commit this file. Set `VITE_API_BASE_URL` to the backend URL when the frontend and API are hosted separately.

Install and start the backend:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Install dependencies and run the API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal at the repository root, install and run the frontend:

```bash
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000` for the API. Confirm backend readiness at `http://localhost:8000/health`.

## Production deployment

Deploy the frontend and backend as separate services. Set the frontend's `VITE_API_BASE_URL` to the public backend URL at build time. Set backend environment variables in the deployment platform's secret manager—do not upload `.env`.

Backend production startup command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For container-based backend deployment:

```bash
docker build -t charak-api ./backend
docker run --rm -p 8000:8000 --env-file .env charak-api
```

The Docker image exposes port 8000 and honors the platform-provided `PORT`. If using SQLite in production, mount persistent storage and set `DATABASE_URL` to its absolute path; use a managed database before horizontally scaling the API.

The existing Vite configuration builds a Cloudflare Nitro module. Build it and, after configuring the Cloudflare credentials outside the repository, deploy the generated frontend with:

```bash
npm ci
npm run build
npx nitro deploy --prebuilt
```

Allow the frontend domain in the backend's `CORS_ORIGINS` setting, for example `https://app.example.com`.

## Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Frontend | Public backend base URL |
| `GROQ_API_KEY` | Backend | Enables Groq LLM and vision integration |
| `GROQ_MODEL` | Backend | Chat model identifier |
| `GROQ_VISION_MODEL` | Backend | Vision model identifier |
| `CORS_ORIGINS` | Backend | Comma-separated allowed frontend origins |
| `DATABASE_URL` | Backend | SQLAlchemy database connection URL |

The backend reads environment variables first, then `backend/.env` and the project-root `.env`. `GROQ_API_KEY` is optional for local deterministic fallback; configure it for production AI functionality. The application never logs the key.

## Testing and validation

```bash
cd backend
pytest
```

```bash
npm run lint
npm run build
```

## Git workflow

```bash
git init
git add .
git status
git commit -m "Prepare Charak for deployment"
```

Before each commit, inspect `git status` and confirm that `.env`, virtual environments, SQLite databases, and build output are absent. Use feature branches, test locally, merge reviewed changes, then redeploy from the selected deployment platform. Do not force-push published Lovable history.

## Troubleshooting

- **Frontend cannot reach the API:** ensure the backend is running, `VITE_API_BASE_URL` is correct, and the frontend origin appears in `CORS_ORIGINS`.
- **LLM responses use fallback behavior:** add a valid `GROQ_API_KEY` through `.env` locally or deployment secrets in production.
- **Database resets after deployment:** persist the SQLite file with a volume or configure a production database using `DATABASE_URL`.
- **Port binding fails in deployment:** use the documented backend command; it binds to the platform's `PORT`.

## Security and clinical-safety notes

- `.env` files are ignored by Git; `.env.example` contains placeholders only.
- Keep all provider keys and production connection strings in local environment files or the deployment secret manager.
- Charak provides healthcare navigation assistance, not a medical diagnosis or replacement for licensed clinical care. For urgent symptoms, seek immediate professional emergency assistance.
