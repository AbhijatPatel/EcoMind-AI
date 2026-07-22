# EcoMind AI — Personal Sustainability Intelligence Assistant

> Status: frontend, backend, and Dockerization are built. AWS deployment prep
> is not yet done. See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full
> system design.

## 1. Overview

EcoMind AI helps individuals and organizations understand their
environmental footprint — across transportation, food, energy, and
shopping/waste habits — and get personalized, realistic recommendations for
reducing it.

## 2. Problem Statement

Most people want to live more sustainably but lack a simple way to (a)
quantify their actual environmental impact and (b) translate that into
small, achievable changes. EcoMind AI closes that gap with a deterministic
carbon-footprint engine plus an AI assistant that explains the numbers and
suggests next steps.

## 3. Features

- Carbon footprint calculator (0–100 score, works for guests or logged-in users)
- AI sustainability chatbot with real-time streaming responses
- Personalized daily/weekly/monthly sustainability plan, targeted at your weakest categories
- Weekly eco-challenge generator, with completion tracking
- Progress dashboard with score history chart
- Full account management: register/login, password change, account deletion

## 4. Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system diagram and
design rationale. In short: a React SPA talks only to a FastAPI backend,
which is the sole component with access to the LLM provider and the
database.

## 5. Technology Stack

| Layer      | Technology                          |
|------------|---------------------------------------|
| Frontend   | React, Vite, Tailwind CSS, React Router |
| Backend    | Python, FastAPI, SQLAlchemy (async)   |
| AI         | Anthropic Claude API                  |
| Database   | PostgreSQL (SQLite supported for tests/dev) |
| Container  | Docker, Docker Compose                |
| Deployment | AWS App Runner (not yet configured)   |

## 6. Repository Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md#3-folder-structure) for the
annotated folder tree.

## 7. Running locally with Docker (recommended)

This is the fastest way to run the whole stack — frontend, backend, and a
real Postgres database — with one command.

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Copy the root env file and fill in at least ANTHROPIC_API_KEY
cp .env.example .env

# 2. Start everything
docker compose up --build
```

Then open:
- Frontend: http://localhost:3000
- Backend docs (Swagger UI): http://localhost:8000/docs
- Backend health check: http://localhost:8000/health

The database schema is created automatically on first boot (see
`AUTO_CREATE_TABLES` in [ARCHITECTURE.md](./ARCHITECTURE.md) for why, and
its limits). To stop everything: `docker compose down`. To also wipe the
database volume: `docker compose down -v`.

**Without a real ANTHROPIC_API_KEY**, every feature works except AI chat —
the calculator, plan generator, challenges, and dashboard don't depend on
the LLM at all (see `carbon_engine.py` / `plan_generator.py` /
`challenge_generator.py`, which are deliberately deterministic, not
LLM-driven).

## 8. Running locally without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
cp .env.example .env   # set DATABASE_URL to a local Postgres, or use SQLite for a quick try:
#   DATABASE_URL=sqlite+aiosqlite:///./dev.db
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
The dev server runs on http://localhost:5173. Set `VITE_API_BASE_URL` in a
`frontend/.env` file if your backend isn't on `http://localhost:8000`.

**Backend tests:**
```bash
cd backend
python3 -m pytest tests/ -v
```

## 9. Environment Variables

See `backend/.env.example` for backend variables (database, JWT secret, AI
provider key, CORS) and the root `.env.example` for the variables
`docker-compose.yml` itself reads (ports, Postgres credentials, and the
`VITE_API_BASE_URL` baked into the frontend build).

## 10. AWS Deployment

Not yet done. Planned target is AWS App Runner — see
[ARCHITECTURE.md](./ARCHITECTURE.md) for the phase roadmap.

## 11. Future Improvements

- AWS App Runner deployment (HTTPS, CloudWatch logging, budget alerts)
- Alembic migrations, replacing the current dev-only auto-create-tables step
- Conversation windowing for long chat histories (flagged in `documentation/prompt-strategy.md`)
- Multi-language support
- Organization/team dashboards with aggregate impact reporting
