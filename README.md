# Anonymous Feedback Portal

An internal web app for employees to submit anonymous confessions/queries plus a
fixed set of experience questions, with an admin dashboard for reviewing
submissions, device/request logs, and statistics (including repeated-name and
repeated-device detection).

## Architecture

```
React (Vite/TS) ── frontend, no login for employees
        │  fetch (JSON, credentials: include)
        ▼
FastAPI backend ── cloud-hosted
        │  asyncpg over VPN / SSH tunnel
        ▼
PostgreSQL ── your on-prem server
```

- **Backend**: FastAPI, async SQLAlchemy 2.0, Alembic migrations, JWT admin
  sessions in an httpOnly cookie, `slowapi` rate limiting on the public endpoint.
- **Frontend**: React + TypeScript (Vite), React Router. No build-time coupling
  to the question set - questions are seeded in the DB and fetched at runtime,
  so adding/editing questions doesn't require a frontend deploy.
- **Database**: PostgreSQL. Runs on your own server; the cloud-hosted backend
  connects to it directly over a VPN/SSH tunnel you provision (see
  `backend/.env.example` → `DATABASE_URL`). **Your network/security team should
  confirm the tunnel setup** before this goes live - the backend has no
  visibility into how that connection is secured.

## Important trade-offs (read before deploying)

These were explicit decisions made with the requester; flagging them again here
for whoever reviews this before go-live, per standard security/management
sign-off:

1. **No access gate on the public form.** Per the chosen requirement, the
   submission page has no passphrase or network restriction - only rate
   limiting (`SUBMIT_RATE_LIMIT`, default 5/hour/IP), a honeypot field, and a
   minimum-fill-time check to blunt bots. It is reachable by anyone with the
   URL. If that's broader than intended, put it behind your VPN/reverse proxy
   IP allowlist, or ask to add a shared passphrase - both are small, additive
   changes to `app/routers/public.py` / the login flow.
2. **Device data is IP + browser-reported signals only.** No browser exposes a
   visitor's OS username, computer name, or MAC address to a website, on any
   OS or browser - this is a platform-level restriction, not something this
   app chose to skip. What's actually captured per submission: IP address,
   user-agent, screen resolution, timezone, browser language, and a
   locally-computed device fingerprint hash (for repeat-submission detection
   only, re-hashed server-side). See `frontend/src/utils/fingerprint.ts` and
   `backend/app/models.py`.
3. **This narrows "anonymous."** Logging IP address and a device fingerprint
   alongside free-text confessions means a submission is not fully
   unlinkable to a person - someone with server/DB access and network logs
   could in principle correlate a submission to an employee. If the intent is
   stronger anonymity guarantees (e.g. for compliance or trust reasons),
   consider dropping IP storage, or hashing/truncating it, before launch -
   that's a policy call for engineering/HR/legal, not a technical default this
   app should assume.
4. **Repeated-name detection is a heuristic, not NLP/NER.** It flags
   capitalized word runs in free text (`backend/app/name_extraction.py`) and
   will both miss real names and occasionally flag non-names. Treat its output
   as a lead for the admin to open the linked submissions and judge in
   context - not a verified identification. An upgrade path (spaCy or a local
   LLM via Ollama) is noted in that file if precision needs to improve.

## Local development

**Backend**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then edit DATABASE_URL, JWT_SECRET, admin bootstrap creds
```
Start Postgres for local dev: `docker compose up -d` (root of repo) - it
publishes on `localhost:5442`, not 5432, to avoid colliding with a native
Postgres install some machines already have running on 5432. See
[SETUP.md](SETUP.md) for the full walkthrough and troubleshooting.
```bash
alembic upgrade head
uvicorn app.main:app --reload
```
API docs at `http://localhost:8000/docs`. On first startup the app seeds the
10 default questions and creates the bootstrap admin from `.env` if none exists.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`
in dev (see `vite.config.ts`), so no `.env` is needed locally.

## Deployment notes

- Set `COOKIE_SECURE=true` once served over HTTPS (required for the admin
  session cookie to be sent).
- The admin session cookie is `SameSite=Lax`, which browsers send on
  cross-origin requests as long as frontend and backend share the same
  registrable domain (e.g. `app.company.com` + `api.company.com` both under
  `company.com` - fine). If they end up on **unrelated domains**, the cookie
  won't be sent and admin login will silently fail on every request - either
  put both under one domain, or change the cookie to `SameSite=None` (with
  `COOKIE_SECURE=true`, which HTTPS requires anyway) in `app/security.py` /
  `app/routers/admin.py`.
- Set `FRONTEND_ORIGINS` to your deployed frontend's exact origin(s).
- Set `TRUST_PROXY_HEADERS=true` only if your reverse proxy/load balancer sets
  `X-Forwarded-For` and strips any client-supplied one - otherwise IP logging
  can be spoofed.
- Rotate `JWT_SECRET` and the bootstrap admin password before go-live; the
  bootstrap admin is only created once (idempotent) so changing `.env` after
  first run won't reset an existing admin's password.
- The 10 questions can currently only be changed by editing
  `backend/app/seed_questions.py` and inserting/updating rows directly (or via
  a migration) - there is no admin UI for question management yet.

## Repo layout

```
backend/    FastAPI app, Alembic migrations, Dockerfile
frontend/   React + TypeScript app (Vite), Dockerfile + nginx.conf
docker-compose.yml   local Postgres only (dev)
```
