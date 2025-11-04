Great — below are **task-oriented prompts** you can drop straight into your orchestration system or hand to an Implementation Agent.
They’re designed so each **task is independent** (can be run alone) **or** you can hand the agent the entire list to execute sequentially. Each task includes: **ID, objective, inputs, expected outputs, acceptance criteria, implementation notes, and dependencies**.

Use the **full combined prompt** when you want the agent to run everything end-to-end, or copy any single **Task block** to run only that task.

---

# ▶️ Full Combined Prompt (run all tasks in order)

```
You are an Implementation Agent. Execute the following ordered tasks to build the "America’s Got Talent" voting POC. Tasks are independent and idempotent; any task can be run alone or all tasks can be executed sequentially. For each task, produce code/artifacts, a short status report, and unit tests where applicable. Log all prompts, iterations, and decisions.

Tasks to run in order:
1. TASK-001: Create project skeleton (backend + frontend)
2. TASK-002: Define DB schema & migrations (Postgres)
3. TASK-003: Implement backend models and DB layer
4. TASK-004: Implement Redis cache & in-memory fallback
5. TASK-005: Implement /vote endpoint with atomic enforcement (DB transaction or Redis Lua)
6. TASK-006: Implement nonce handling and rate-limiter middleware
7. TASK-007: Add logging, metrics (/metrics), and health (/health)
8. TASK-008: Implement mocked CAPTCHA/SMS escalation hooks
9. TASK-009: Implement Next.js frontend (single input + fingerprint, nonce)
10. TASK-010: Dockerize services and create docker-compose.yml
11. TASK-011: Write backend unit & integration tests (pytest)
12. TASK-012: Write frontend tests (@testing-library/react)
13. TASK-013: Run full test suite and produce test report
14. TASK-014: Produce README, .env.example, and implementation transcript (prompt logs & iterations)

Follow acceptance criteria for each task (see individual task definitions). If a task fails tests, iterate until green, log attempts, and produce a short post-mortem note.

Outputs to deliver: repository at /project-root with structure, passing tests, Docker Compose run instructions, README, .env.example, and an implementation transcript of prompts, iterations, and final decisions.
```

---

# 🔧 Individual Task Prompts (copy any single one to run independently)

---

### TASK-001 — Create project skeleton (backend + frontend)

**Objective:** Create the repository skeleton and initial files.
**Inputs:** none
**Expected outputs:**

```
/project-root
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/index.tsx
│   ├── components/
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

**Acceptance criteria:**

* Files and folders created with placeholder README in backend and frontend.
* `requirements.txt` includes FastAPI, uvicorn, asyncpg, redis, sqlalchemy, alembic, pytest.
* Frontend package.json includes Next.js and testing deps.
  **Implementation notes:**
* Initialize git repo, create .gitignore.
* Provide short status report and next-step checklist.

---

### TASK-002 — Define DB schema & migrations (Postgres)

**Objective:** Create migration files and SQLAlchemy models (Contestant, DeviceToken, Vote).
**Inputs:** DB connection string (use env var placeholder).
**Expected outputs:**

* SQLAlchemy models in `backend/models.py`.
* Alembic migration scripts creating tables with:

  * `DeviceToken.total_votes` CHECK `<=3`
  * `UNIQUE (contestant_id, device_token_id)` on Vote
* README section describing how to run migrations.
  **Acceptance criteria:**
* Models importable by backend.
* Migration script runs locally (mocked DB or instructions).
  **Implementation notes:**
* Use UUID primary keys and timestamps (UTC).
* Add indexes per design (DeviceToken.token, Vote.voted_at).

---

### TASK-003 — Implement backend models and DB layer

**Objective:** Implement DB access layer and helper services to create/find contestants, device tokens, and insert votes within transactions.
**Inputs:** models from TASK-002
**Expected outputs:**

* `backend/services/db.py` with async functions:

  * `get_or_create_device_token(hashed_token)`
  * `get_contestant_by_last_name(last_name_normalized)`
  * `record_vote_tx(contestant_id, device_token_id)` — atomic
* Example usage in main app.
  **Acceptance criteria:**
* `record_vote_tx` performs atomic insert and raises on unique constraint violation.
* Provide unit tests mocking DB.

---

### TASK-004 — Implement Redis cache & in-memory fallback

**Objective:** Provide a cache abstraction used for rate-limiting, nonces, and temporary counters.
**Inputs:** REDIS_URL env var (placeholder)
**Expected outputs:**

* `backend/services/cache.py` with `Cache` class:

  * Uses aioredis if configured; otherwise an in-memory async-safe store.
  * Methods: `setnx(key, value, ttl)`, `incr(key)`, `get(key)`, `set(key, ttl)`, `eval_lua(script, keys, args)` if Redis available.
    **Acceptance criteria:**
* Cache abstraction works in tests with both redis and fallback.
* Document how to disable Redis for local dev.

---

### TASK-005 — Implement /vote endpoint with atomic enforcement

**Objective:** Implement POST /vote following spec; ensure atomic enforcement for vote limits (1 per contestant, max 3).
**Inputs:** DB services (TASK-003), cache (TASK-004)
**Expected outputs:**

* `backend/routes/vote.py` exposing POST /vote
* Hash fingerprint (SHA-256 + SALT from env)
* Nonce validation via cache `SETNX` TTL 5 min
* Rate-limit checks before DB op
* Atomic vote: either use DB transaction (`SELECT ... FOR UPDATE`) to increment `DeviceToken.total_votes` and then insert Vote, or use a Redis Lua script to check and increment in one atomic step then persist to DB.
* Graceful handling of duplicate-key error => return 200 "Vote already recorded" or 400 per spec.
  **Acceptance criteria:**
* Unit tests simulate:

  * Duplicate vote prevention
  * Total votes <= 3
  * Concurrent submissions: spawn parallel requests and assert invariants
* Endpoint returns appropriate HTTP statuses.

---

### TASK-006 — Implement nonce handling and rate-limiter middleware

**Objective:** Middleware that enforces IP and device rate limits and nonce uniqueness.
**Inputs:** cache abstraction
**Expected outputs:**

* Middleware integrated into FastAPI app that:

  * Enforces IP rate limit (5/min default) using token-bucket or sliding window in Redis
  * Enforces device vote limit checks (use cache for temporary counters)
  * Validates nonce via `setnx`, rejects reused nonces
* Configuration via env vars
  **Acceptance criteria:**
* Middleware unit tests: rate limit triggers 429 after threshold, nonce reuse returns 400.

---

### TASK-007 — Add logging, metrics (/metrics), and health (/health)

**Objective:** Instrument the app with structured logging and observability endpoints.
**Inputs:** Logging config env vars
**Expected outputs:**

* `/health` endpoint returning JSON status
* `/metrics` endpoint exposing basic Prometheus metrics (request count, vote success/fail counters)
* Structured logging to stdout with audit fields (hashed_token, masked IP, timestamp, action)
  **Acceptance criteria:**
* Metrics endpoint is reachable; logs contain required fields and mask raw fingerprints.

---

### TASK-008 — Implement mocked CAPTCHA/SMS escalation hooks

**Objective:** Create stubs that simulate escalation flows when suspicious.
**Inputs:** configuration flag `ENABLE_ESCALATION=false` by default
**Expected outputs:**

* Endpoint or response payload that indicates a challenge: `{ "status":"challenge", "type":"captcha" }`
* Configurable switch to simulate SMS OTP flow.
  **Acceptance criteria:**
* When escalation flag triggered by heuristics (e.g., >3 failures), endpoint returns challenge JSON and backend records the event in logs.

---

### TASK-009 — Implement Next.js frontend (single input + fingerprint + nonce)

**Objective:** Minimal UI that submits votes.
**Inputs:** backend URL env var
**Expected outputs:**

* `frontend/pages/index.tsx` with:

  * Text input for last_name
  * Submit button
  * Uses FingerprintJS (or a lightweight fingerprint generator) for fingerprint
  * Generates nonce (timestamp + random)
  * Calls POST /vote and shows success or error message only
* Basic frontend test verifying submission flow
  **Acceptance criteria:**
* Submission works against running backend (Docker Compose).
* UI shows only success or error; no extra debug info.

---

### TASK-010 — Dockerize services and create docker-compose.yml

**Objective:** Make the system runnable with docker-compose.
**Inputs:** built backend & frontend
**Expected outputs:**

* Dockerfiles for backend and frontend
* `docker-compose.yml` with services: backend (8000), frontend (3000), postgres, redis
* `.env.example` with placeholders for DB_URL, REDIS_URL, SALT, RATE_LIMITS
  **Acceptance criteria:**
* `docker-compose up --build` brings up all services (DB may need migrations run; include a script to run migrations).

---

### TASK-011 — Write backend unit & integration tests (pytest)

**Objective:** Create test suite for backend behaviors.
**Inputs:** endpoints and services implemented
**Expected outputs:**

* Tests covering:

  * hash function correctness
  * nonce SETNX behavior
  * vote insertion and limit enforcement
  * concurrency tests (e.g., use pytest-asyncio and httpx to simulate parallel requests)
  * rate limiting behavior
    **Acceptance criteria:**
* Tests run locally with `pytest` and pass (or clearly document environment to run them). Aim for tests that run in CI via Docker Compose.

---

### TASK-012 — Write frontend tests (@testing-library/react)

**Objective:** Basic coverage for form submission UI.
**Inputs:** built frontend
**Expected outputs:**

* Test that:

  * Form renders
  * On submit, fingerprint + nonce created and fetch called
  * Success and error messages display properly
    **Acceptance criteria:**
* Tests run with `npm test` / `yarn test` and pass.

---

### TASK-013 — Run full test suite and produce test report

**Objective:** Execute all tests and collect results.
**Inputs:** test suites from TASK-011 and TASK-012
**Expected outputs:**

* Test report (JUnit or text) summarizing passed/failed tests
* Coverage report (optional)
  **Acceptance criteria:**
* All required tests pass. If not, retry and document failures and fixes.

---

### TASK-014 — Produce README, .env.example, and implementation transcript

**Objective:** Final packaging and evidence.
**Inputs:** repository and logs
**Expected outputs:**

* Root README with setup, run, and test instructions
* `.env.example` with all required env vars
* `IMPLEMENTATION_TRANSCRIPT.md` containing:

  * All prompts used by the agent
  * Iterations and refinements
  * Key decisions and reasoning
  * Build and test logs (summaries)
    **Acceptance criteria:**
* README must include Docker Compose run command, migration steps, and how to run tests.
* Transcript must contain the prompt history and notes sufficient for the reviewers to verify agentic workflow.

---
