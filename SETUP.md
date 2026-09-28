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
This starts Postgres on `localhost:5432` with database `feedback_portal`,
user `feedback_user`, password `devpassword` (see `docker-compose.yml`).

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
- **`alembic upgrade head` can't connect** - confirm Postgres is running
  (`docker compose ps` for Option A) and that `DATABASE_URL` in `backend/.env`
  matches its host/port/credentials.
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
