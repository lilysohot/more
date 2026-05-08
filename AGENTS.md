# AGENTS

## Trust Config First
- README files are stale in a few key places: they still mention `docs/development.md`, a backend on `8000`, and a frontend `pnpm test` command that does not exist.

## OpenCode Assets
- Repo-local OpenCode assets live at the root: `skills/`, `agents/`, and `references/`.
- `.agents/` is a compatibility mirror and is gitignored; prefer editing the root OpenCode files if you want changes tracked.
- There are two unrelated `skills` trees: root `skills/` contains OpenCode skills, while `backend/skills/` is a Python package imported by the backend runtime.
- If you need repo personas or orchestration rules, read `agents/README.md` first.

## Repo Shape
- This repo is two separate apps, not a workspace toolchain. Run commands inside `frontend/` or `backend/`.
- `backend/`: FastAPI app, entrypoint `app/main.py`
- `frontend/`: Vite + React app, entrypoint `src/main.tsx`

## Verified Commands
- Frontend uses `pnpm`.
- Frontend dev: `pnpm dev`
- Frontend verification: `pnpm lint` then `pnpm build` (`build` already runs `tsc`).
- Backend install: `pip install -r requirements.txt`
- Run backend commands from `backend/`; `app/core/config.py` loads `.env` from the current working directory.
- Local backend dev should use port `8123` so the Vite proxy works: `uvicorn app.main:app --reload --port 8123`
- Full stack: `docker-compose up -d`

## Ports And Env
- Local Vite dev server is `5173`; Docker frontend is exposed on `3000`.
- Backend is exposed on `8123` in Docker; do not trust README references to `8000` for host access.
- `frontend/vite.config.ts` proxies `/api/v1` to `http://localhost:8123`.
- `frontend/src/utils/request.ts` uses `VITE_API_BASE_URL` if set, otherwise `/api/v1`.
- `backend/app/core/config.py` falls back to `postgresql://analyst:password@localhost:5432/analyst_db` only in `DEBUG`; this does not match Docker Compose Postgres (`localhost:5433`, DB `moremoney_db`, user `moremoney`).

## Backend Gotchas
- Startup runs `init_db()`, which calls `Base.metadata.create_all()`. Local tables can appear without running Alembic.
- If you change schema, keep `backend/app/models/` and `backend/alembic/versions/` aligned.
- In non-`DEBUG` mode the app refuses to start without `SECRET_KEY`, `ENCRYPTION_KEY`, and `DATABASE_URL`.
- `app/services/analysis.py` is live-data-first now: it resolves and collects via Tushare first, then falls back to EastMoney.
- Redis is optional for active-task tracking; `app/services/analysis.py` falls back to in-memory state when Redis is unavailable.

## Frontend Wiring
- Router lives in `frontend/src/router/index.tsx`.
- Auth gating happens in `frontend/src/components/layout/MainLayout.tsx`.
- Shared API client lives in `frontend/src/utils/request.ts`; it attaches the bearer token and redirects to `/login` on `401`.

## Verification Notes
- There is no frontend test script in `frontend/package.json`.
- Backend tests live under `backend/tests/unit/`.
- A focused backend test file works, e.g. `pytest -q tests/unit/api/test_analysis_progress_helpers.py`.
- `pytest -q` from `backend/` currently fails during collection because `tests/unit/skills/test_tushare_skill.py` collides with stale top-level `__pycache__/test_tushare_skill*.pyc`.

## Topic Docs
- `backend/docs/api-patterns.md`: project-specific rules for FastAPI endpoints and response contracts.
- `backend/docs/database-rules.md`: async SQLAlchemy, schema, migration, and transaction rules.
- `backend/docs/testing-standards.md`: test scope, verification commands, and current repo limits.
- `frontend/docs/page-ui-patterns.md`: page composition, routing, Ant Design/Tailwind usage, and report UI conventions.
- `frontend/docs/state-request-rules.md`: Zustand ownership, API wrappers, shared request client, and contract-sync rules.
- `frontend/docs/verification-rules.md`: frontend verification commands, manual smoke checks, and current test limits.

## Project Planning Docs
- Root project-planning content lives under `docs/`.
- `docs/plans/`: stores project plan checklists. New file names should use the topic-file prefix pattern, e.g. `project_plan_YYYY-MM-DD.md`.
- `docs/progress/`: stores plan execution progress. New file names should use the topic-file prefix pattern, e.g. `project_progress_YYYY-MM-DD.md`.
- Project-specific topic docs currently live directly in `docs/`. If you add a dated project topic doc, its file name should use the topic-file prefix pattern, e.g. `project_doc_YYYY-MM-DD.md`; there is no separate `docs/titles/` directory today.
- `docs/plans/` file format:
- File name: `<topic-file-name>_YYYY-MM-DD.md`, e.g. `project_plan_YYYY-MM-DD.md`
- Content: executable task checklist extracted from project-specific docs.
- Task format: `[x] Task description`, e.g. `[x] Refine backend topic rules`.
- After a task is completed and passes testing and review, change `[x]` to `[√]` and add the completed item to the matching file in `docs/progress/`, e.g. `[√] Refine backend topic rules`.
- `docs/progress/` file format:
- File name: `<topic-file-name>_YYYY-MM-DD.md`, e.g. `project_progress_YYYY-MM-DD.md`
- Content: execution progress for the plan checklist.

## Module Rule Files
- `backend/app/api/AGENTS.md`: route-layer rules and API contract guardrails.
- `backend/app/services/AGENTS.md`: database workflow and transaction-boundary rules.
- `backend/app/models/AGENTS.md`: schema conventions tied to this project.
- `backend/alembic/AGENTS.md`: migration authoring rules.
- `backend/tests/AGENTS.md`: project-specific testing rules.
- `frontend/src/router/AGENTS.md`: route registration and auth-entry rules.
- `frontend/src/pages/AGENTS.md`: page orchestration, navigation, and state-boundary rules.
- `frontend/src/components/AGENTS.md`: component boundary and report UI rules.
- `frontend/src/api/AGENTS.md`: shared HTTP wrapper and typed endpoint rules.
- `frontend/src/store/AGENTS.md`: Zustand state ownership and async workflow rules.
- `frontend/src/utils/AGENTS.md`: request client and helper-function rules.
- `frontend/src/types/AGENTS.md`: backend contract sync and naming rules.
- `frontend/src/styles/AGENTS.md`: global style and report visual-system rules.

## Local Hygiene
- `.env` files are gitignored; the repo already contains local `frontend/.env` and `backend/.env`, so avoid overwriting or committing env changes unless asked.
- Docker backend runs under `debugpy` and exposes `5678`; the shared VS Code attach config is `.vscode/launch.json`.
