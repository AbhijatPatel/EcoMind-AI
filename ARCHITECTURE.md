# EcoMind AI — Architecture (Phase 1)

## 1. System Overview

EcoMind AI is a three-tier application: a React SPA, a FastAPI backend that owns
all business logic and data access, and a PostgreSQL database. The backend is the
only component allowed to talk to the LLM provider, so API keys never reach the
browser.

```
┌─────────────────────┐        HTTPS/JSON         ┌──────────────────────────┐
│   Frontend (SPA)     │ ───────────────────────▶ │   FastAPI Backend         │
│   React + Vite       │ ◀─────────────────────── │   (REST + Streaming)      │
│   Tailwind CSS        │      SSE / chunked        │                          │
└─────────────────────┘                            │  ┌────────────────────┐  │
                                                     │  │ Auth (JWT)         │  │
                                                     │  ├────────────────────┤  │
                                                     │  │ Carbon Engine      │  │
                                                     │  ├────────────────────┤  │
                                                     │  │ AI Service Layer   │──┼──▶  LLM API
                                                     │  ├────────────────────┤  │      (Claude/OpenAI)
                                                     │  │ Challenge Service  │  │
                                                     │  └────────────────────┘  │
                                                     └──────────┬───────────────┘
                                                                │ SQLAlchemy ORM
                                                                ▼
                                                     ┌──────────────────────────┐
                                                     │   PostgreSQL             │
                                                     │   users, profiles,       │
                                                     │   assessments, chats,    │
                                                     │   challenges, progress   │
                                                     └──────────────────────────┘
```

## 2. Design Principles

- **Backend-mediated AI access** — the frontend never calls the LLM directly.
  Every AI call passes through `backend/app/ai/`, where the system prompt,
  safety instructions, and few-shot examples are enforced consistently.
- **Stateless API, stateful data** — auth uses JWT so any backend replica can
  serve any request; durable state (users, assessments, chat history) lives in
  Postgres, not in server memory.
- **Streaming-first chat** — `/chat` uses `StreamingResponse` so the UI can show
  incremental progress ("Analyzing your lifestyle..." → score → recommendations)
  instead of a single blocking reply.
- **Deterministic scoring, generative explanation** — the carbon footprint
  *score* is computed by a plain Python module (`carbon_engine`), not the LLM.
  The LLM explains and personalizes; it does not invent numbers. This keeps
  scores auditable and reproducible.
- **12-factor config** — all secrets and environment-specific values (DB URL,
  API keys, CORS origins) come from environment variables via `.env`, never
  hardcoded.

## 3. Folder Structure

```
ecomind-ai/
├── frontend/                      # React + Vite + Tailwind SPA
│   ├── src/
│   │   ├── components/            # Reusable UI building blocks (cards, nav, charts)
│   │   ├── pages/                 # Route-level views (Landing, Dashboard, Calculator, Chat...)
│   │   ├── hooks/                 # Custom hooks (useAuth, useStreamingChat, useCarbonScore)
│   │   ├── services/              # API client wrappers (fetch/axios calls to backend)
│   │   ├── assets/                # Images, icons, static media
│   │   ├── App.jsx                # Root component + router
│   │   └── main.jsx                # Vite entry point
│   ├── public/                    # Static files served as-is
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── api/routes/             # Route modules: chat.py, carbon.py, plan.py, challenge.py, health.py, auth.py
│   │   ├── core/                   # Config, security (JWT/hashing), CORS, logging setup
│   │   ├── models/                 # SQLAlchemy ORM models (User, Profile, Assessment, ChatLog, Challenge)
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/               # Business logic: carbon_engine.py, plan_generator.py, challenge_generator.py
│   │   ├── db/                     # Session management, Alembic migrations
│   │   ├── ai/                     # LLM client, prompt templates, few-shot examples, safety filters
│   │   ├── main.py                 # FastAPI app instance, router registration, middleware
│   │   └── config.py               # Settings loaded from environment variables
│   ├── tests/                      # Pytest suite (API, carbon engine, auth, AI response handling)
│   ├── requirements.txt
│   └── .env.example
│
├── documentation/
│   └── prompt-strategy.md          # System prompts, iteration history, few-shot design notes
│
├── docker/
│   ├── frontend.Dockerfile
│   └── backend.Dockerfile
│
├── docker-compose.yml               # Orchestrates frontend + backend + postgres
├── .gitignore
├── README.md
└── ARCHITECTURE.md                  # This file
```

## 4. Data Model (planned for Phase 5)

| Table         | Purpose                                              |
|---------------|-------------------------------------------------------|
| `users`       | Auth identity (email, hashed password, created_at)    |
| `profiles`    | Lifestyle inputs (transport, diet, energy, habits)     |
| `assessments` | Historical carbon scores + category, tied to a profile snapshot |
| `chat_logs`   | AI conversation turns, tied to a user, for continuity and audit |
| `challenges`  | Generated weekly eco-challenges and completion status  |
| `progress`    | Time-series of score changes for the dashboard chart   |

## 5. Request Flow Example — `/chat`

1. Frontend sends `POST /chat` with the user's message and auth token.
2. Backend validates the JWT, loads recent profile/context from Postgres.
3. `ai/prompt_builder.py` assembles: system prompt + user profile context +
   few-shot examples + the new user message.
4. `ai/client.py` streams the LLM response back as Server-Sent chunks.
5. FastAPI wraps this in a `StreamingResponse`; the frontend reads it with the
   `ReadableStream` API and renders tokens as they arrive.
6. On completion, the full exchange is persisted to `chat_logs`.

## 6. Phase Roadmap

| Phase | Deliverable                                   | Status        |
|-------|------------------------------------------------|---------------|
| 1     | Architecture & folder structure                | ✅ This step   |
| 2     | Frontend (pages, components, styling)          | Next          |
| 3     | Backend (routes, schemas, error handling)      | Pending       |
| 4     | AI integration (prompts, streaming)            | ✅ Complete    |
| 5     | Database (models, migrations)                  | ✅ Models complete; migrations not yet (see §7 below) |
| 6     | Dockerization                                   | ✅ Complete    |
| 7     | AWS App Runner deployment                       | Pending       |

Each phase will only touch the files relevant to it, and I'll summarize what
changed and why before moving to the next one.

## 7. Known shortcuts (not yet addressed)

- **No Alembic migrations yet.** The app auto-creates missing tables on
  startup (`AUTO_CREATE_TABLES`, see `backend/app/main.py`) — this is a
  deliberate Docker/dev convenience so `docker compose up` works against a
  fresh Postgres volume with zero manual steps, but it only adds missing
  tables and never alters existing ones. A real schema change (e.g. adding a
  column to an existing table) would need a manual migration or a
  hand-written `ALTER TABLE`, not this mechanism. Alembic should replace this
  before any production use with an evolving schema.
- **Conversation windowing for chat is unimplemented** — flagged in
  `documentation/prompt-strategy.md`. Long chat histories would grow the
  prompt (and therefore cost/latency) unbounded.
- **The Postgres connection path (asyncpg) has not been tested against a
  real running Postgres instance** in this development environment — only
  against SQLite. The connection string format and pooling logic
  (`backend/app/db/session.py`) follow the standard asyncpg URL scheme, but
  this is worth a real smoke test the first time `docker compose up` is run
  somewhere with Docker available.

