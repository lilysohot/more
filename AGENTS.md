# AGENTS

## Trust These Sources First
- Prefer executable config over prose. Several docs are stale: they still mention `docs/development.md`, `pnpm test`, and a backend on port `8000`.

## Installed Skills
- OpenCode project-local skills are installed in the root `skills/` directory, with supporting material in `references/` and reviewer personas in `agents/`.
- This project also retains a mirrored `.agents/` copy for compatibility with prior local conventions.
- When a request matches one of the installed `addyosmani/agent-skills`, prefer the root-level OpenCode layout first rather than re-deriving the workflow from scratch.

## Repo Shape
- This repo is not a monorepo toolchain; it is two separate apps:
- `backend/`: FastAPI app, entrypoint `app/main.py`
- `frontend/`: Vite + React app, entrypoint `src/main.tsx`

## Verified Commands
- Frontend uses `pnpm` (`frontend/pnpm-lock.yaml` exists).
- Frontend dev: `pnpm dev`
- Frontend lint: `pnpm lint`
- Frontend build: `pnpm build`
- Backend install: `pip install -r requirements.txt`
- Backend dev server for local frontend proxy: `uvicorn app.main:app --reload --port 8123`
- Docker full stack: `docker-compose up -d`

## Ports And Routing
- For local frontend dev, do not assume backend port `8000`.
- `frontend/vite.config.ts` proxies `/api/v1` to `http://localhost:8123`.
- `frontend/src/utils/request.ts` uses `VITE_API_BASE_URL` if set, otherwise falls back to `/api/v1`.
- `docker-compose.yml` exposes backend on host port `8123` and frontend on `3000`.

## Backend Gotchas
- Startup runs `init_db()` from `app.database`, which calls `Base.metadata.create_all()`. Local tables may appear without running Alembic.
- Alembic is still present in `backend/alembic/`; if you change schema, keep models and migrations aligned.
- Required backend secrets are enforced in `backend/app/core/config.py`. In non-`DEBUG` mode the app raises on missing `SECRET_KEY`, `ENCRYPTION_KEY`, or `DATABASE_URL`.
- Redis is optional for active task tracking: `app/services/analysis.py` falls back to in-memory task storage if Redis is unavailable.
- The current analysis flow is not using live data collection yet. `app/services/analysis.py` explicitly skips collection and ratio calculation and uses mock data/ratios before the LLM/report steps.

## Frontend Wiring
- Router lives in `frontend/src/router/index.tsx`.
- Auth is enforced in `frontend/src/components/layout/MainLayout.tsx` by checking `localStorage` token state and redirecting to `/login`.
- Shared API client is `frontend/src/utils/request.ts`; it attaches the bearer token and redirects to `/login` on `401`.

## Verification Reality
- There is no working frontend test command in `frontend/package.json`.
- `backend/tests/` and `frontend/tests/` are currently empty, so README test instructions are not a reliable verification path.
- For frontend changes, prefer `pnpm lint` and `pnpm build`.

## Local Environment Hygiene
- `.gitignore` ignores `.env`, and this repo already contains local `.env` files. Read them if needed, but do not overwrite or commit env changes unless the user asks.

## Debugging
- Docker backend runs under `debugpy` and exposes port `5678`.
- VS Code attach config is already checked in at `.vscode/launch.json`.
