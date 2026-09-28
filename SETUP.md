# Setup guide

Step-by-step instructions to run the Anonymous Feedback Portal locally. For
architecture and deployment trade-offs, see [README.md](README.md).

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| PostgreSQL | 16 (or Docker Desktop to run it in a container) | `psql --version` or `docker --version` |

## 1. Database

Pick one:

**Option A - Docker (recommended for local dev)**
```bash
docker compose up -d
```
This starts Postgres on `localhost:5442` (deliberately not 5432 - see the
comment in `docker-compose.yml`: many machines already have a native Postgres
service listening on 5432, and reusing that port leads to exactly the
confusing situation in the Troubleshooting section below) with database
`feedback_portal`, user `feedback_user`, password `devpassword`.

**Option B - a Postgres you already have**
Create a database and user yourself, e.g.:
```sql
CREATE USER feedback_user WITH PASSWORD 'devpassword';
CREATE DATABASE feedback_portal OWNER feedback_user;
```
Then use that connection's host/port/credentials in step 2 below instead of
the Option A defaults.

## 2. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
```
Activate the virtual environment:
```bash
# Windows (PowerShell / Git Bash)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```
Install dependencies and configure environment variables:
```bash
pip install -r requirements.txt
cp .env.example .env
```
Open `backend/.env` and check/edit at minimum:
- `DATABASE_URL` - matches whatever you set up in step 1
- `JWT_SECRET` - replace with a long random string
- `ADMIN_BOOTSTRAP_USERNAME` / `ADMIN_BOOTSTRAP_PASSWORD` - the admin login
  created automatically the first time the app starts

Apply migrations and start the server:
```bash
alembic upgrade head
uvicorn app.main:app --reload
```
Backend is now running at `http://localhost:8000` (interactive API docs at
`http://localhost:8000/docs`). On first startup it also seeds the 10 default
questions and creates the bootstrap admin account from `.env`.

Verify it's up:
```bash
curl http://localhost:8000/api/health
```

## 3. Frontend (React)

In a **new terminal**, from the repo root:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. No `.env` is needed for local dev - Vite proxies
`/api` requests to `http://localhost:8000` automatically (see
`frontend/vite.config.ts`). If your backend runs on a different host/port,
copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

## 4. Try it out

- Public form: `http://localhost:5173` - submit a test confession/query and
  answer the 10 questions.
- Admin dashboard: `http://localhost:5173/admin/login` - sign in with the
  `ADMIN_BOOTSTRAP_USERNAME` / `ADMIN_BOOTSTRAP_PASSWORD` you set in
  `backend/.env`. From there: Submissions, Statistics, and Repeated names.

## Troubleshooting

- **`ValueError: password cannot be longer than 72 bytes` on startup** - a
  known `passlib`/`bcrypt` version conflict. `requirements.txt` already pins
  `bcrypt==4.0.1`; if you still hit this, run
  `pip install "bcrypt==4.0.1" --force-reinstall`.
- **Admin login succeeds but every subsequent admin request 401s** - the
  session cookie isn't reaching the backend. Usually a `FRONTEND_ORIGINS`
  mismatch in `backend/.env` (must exactly match the frontend's origin) or,
  in production, a cross-domain cookie issue - see the "SameSite" note in
  README.md.
- **`alembic upgrade head` can't connect, or hangs and fails with
  `OSError: [WinError 121] The semaphore timeout period has expired`** - this
  means `DATABASE_URL` in `backend/.env` is still pointing at the placeholder
  host from `.env.example` (or some other unreachable address), not your local
  database. Set it to
  `postgresql+asyncpg://feedback_user:devpassword@localhost:5442/feedback_portal`
  for Option A (Docker), and confirm the container is up with
  `docker compose ps`.
- **pgAdmin doesn't show `feedback_portal`, or only shows unfamiliar
  databases like `postgres`/`hub`** - you're very likely looking at a
  *different, pre-existing* Postgres server (many Windows dev machines have
  one installed as a service on port 5432 already), not the Docker container
  this project starts. In pgAdmin, register a **new** server specifically for
  this project: Host `localhost`, Port `5442`, Maintenance database
  `feedback_portal`, Username `feedback_user`, Password `devpassword`. Don't
  reuse an existing "PostgreSQL" server entry unless you've checked it's
  actually pointed at port 5442.
- **`alembic upgrade head` (or the app) gets
  `password authentication failed for user "feedback_user"` even though
  `docker-compose.yml` has the right password** - Postgres only applies
  `POSTGRES_USER`/`POSTGRES_PASSWORD` the *first* time it initializes an empty
  data directory. If you'd previously brought the container up with different
  values (or an older version of this file), the named volume already has
  credentials baked in and ignores the current ones - the container logs
  (`docker logs anonymous-feedback-portal-postgres-1`) will show
  `Skipping initialization` on startup if this is what's happening. Since this
  is just a local dev DB, the fix is to wipe it and let it re-init:
  `docker compose down -v && docker compose up -d` (the `-v` removes the
  volume - don't do this if you've since put real data in it).
- **Port already in use** - something else on this machine already owns
  `8000` or `5173`. Run the backend with `--port <other>` / frontend with
  `npm run dev -- --port <other>`, and update `frontend/vite.config.ts`'s
  proxy target (or `VITE_API_BASE_URL`) to match.
- **Questions list is empty** - the seed only runs once, when the `questions`
  table is empty. If you need to reset it, truncate that table and restart
  the backend, or insert rows from `backend/app/seed_questions.py` manually.

## Production deployment

See [README.md](README.md) → "Deployment notes" for `COOKIE_SECURE`,
`TRUST_PROXY_HEADERS`, the VPN/tunnel requirement for the database, and the
Dockerfiles under `backend/` and `frontend/`.
