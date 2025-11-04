# System Design: America's Got Talent Voting System

## 1. System Overview
This system provides a secure, web-based voting platform for "America's Got Talent," allowing users to vote for contestants by submitting their last name via a minimal frontend interface. The backend enforces strict voting rules—limiting each device to one vote per contestant and a maximum of three votes total—while incorporating fraud prevention through device fingerprinting, IP rate limiting, and conceptual escalation for suspicious activity. Votes are stored securely in a database, ensuring integrity and auditability, with the overall design prioritizing scalability for high-traffic events while maintaining simplicity for a proof-of-concept implementation.

## 2. Architecture
The system follows a client-server architecture with a Next.js frontend for the user interface, a FastAPI backend for business logic and API handling, and a PostgreSQL database for persistent storage. A Redis cache is used for performance-critical operations like device tracking and rate limiting, with an in-memory fallback option for simplified deployments. The frontend interacts with the backend via RESTful APIs over HTTPS, sending vote requests with device fingerprints generated client-side (e.g., using a library like FingerprintJS). The backend validates inputs, checks vote limits using cached device tokens, and persists valid votes to the database. Security layers include middleware for rate limiting and conceptual hooks for external verification services (e.g., CAPTCHA or SMS, mocked in MVP). Data flows unidirectionally: frontend to backend for votes, with backend querying the database and cache as needed. For scalability, the backend can be deployed behind a load balancer, with horizontal scaling of API instances.

Architecture Diagram Description (Textual Representation):
- **Frontend (Next.js)**: Handles UI rendering and client-side fingerprint generation → Sends API requests.
- **Backend (FastAPI)**: Receives requests → Validates (rate limit, fingerprint) → Queries/Updates Database & Cache → Responds.
- **Cache (Redis, with in-memory fallback)**: Stores device tokens and vote counts for quick lookups.
- **Database (PostgreSQL)**: Stores contestants, votes, and device tokens.
- **External Services (Conceptual Hooks)**: Mocked CAPTCHA/SMS providers for fraud escalation in future iterations.
Interactions are synchronous for vote submission, with asynchronous logging for audits.

## 3. Data Models
The system uses relational data models in PostgreSQL, with entities designed for efficient querying and integrity constraints.

- **Contestant**: Represents a participant.
  - Fields: id (UUID, primary key), last_name (string, unique, indexed), created_at (timestamp).
  
- **DeviceToken**: Tracks unique devices via hashed fingerprints.
  - Fields: id (UUID, primary key), token (string, unique, hashed fingerprint), total_votes (integer, default 0), created_at (timestamp), last_activity (timestamp).
  - Constraints: CHECK (total_votes <= 3) to enforce vote limit at the database level.
  
- **Vote**: Records each vote instance.
  - Fields: id (UUID, primary key), contestant_id (UUID, foreign key to Contestant), device_token_id (UUID, foreign key to DeviceToken), voted_at (timestamp).
  - Constraints: Unique composite index on (contestant_id, device_token_id) to prevent duplicate votes per device-contestant pair.

Relationships:
- One-to-Many: DeviceToken → Votes (a device can have multiple votes, up to 3 total).
- One-to-Many: Contestant → Votes (a contestant can receive multiple votes).
- Indexes: On Vote.voted_at for time-based queries; on DeviceToken.token for fast lookups. Denormalize contestant vote counts if query performance becomes an issue in production.
Data flow: On vote submission, backend hashes the fingerprint to create/query DeviceToken, increments total_votes if under limit, and inserts Vote if no duplicate exists.

## 4. API Design
The backend exposes a single primary endpoint for voting, with additional health-check endpoints. All APIs use JSON payloads, require HTTPS, and include CORS headers for frontend integration. To prevent replay attacks, include a client-generated nonce (e.g., timestamp + random) in requests, validated for uniqueness per device.

- **POST /vote**
  - Parameters: Body { "last_name": string (required, min 2 chars, max 50 chars), "fingerprint": string (required, client-generated raw fingerprint), "nonce": string (required, unique per request) }.
  - Validation: Sanitize inputs (strip whitespace, lowercase last_name for matching); check contestant existence via database query; hash fingerprint (e.g., SHA-256 with per-environment salt stored in env vars) to generate token; enforce device limits (query DeviceToken for total_votes < 3 and no existing Vote for this contestant); verify nonce hasn't been used recently (store in Redis for short TTL, e.g., 5 min).
  - Responses:
    - 200 OK: { "status": "success", "message": "Vote recorded" }.
    - 400 Bad Request: { "status": "error", "message": "Invalid contestant name" or "Vote limit reached" or "Invalid nonce" }.
    - 429 Too Many Requests: { "status": "error", "message": "Rate limit exceeded" } (with exponential backoff suggestion).
    - 500 Internal Server Error: Generic error for unexpected failures.
  - Constraints: Rate-limited by IP (e.g., 5 requests/min) and device token (e.g., 3 votes total).

- **GET /health**: No params; returns 200 OK { "status": "healthy" } for monitoring.

Integration: Frontend collects fingerprint and generates nonce on load, submits on form submission; backend handles all validation synchronously.

## 5. Security and Fraud Prevention
Security emphasizes vote integrity through multi-layered defenses, simplified for MVP:
- **Device Fingerprinting**: Client generates fingerprint (e.g., via FingerprintJS, including browser/OS metrics); backend hashes it with environment-specific salt to create a persistent token, stored in DeviceToken. Tokens rotate periodically (e.g., every 30 days via last_activity check) to mitigate stale fingerprints. This enforces per-device limits without user accounts.
- **IP-Based Rate Limiting**: Use middleware to limit requests per IP (e.g., 5 votes/min/IP globally, 1 vote/min per endpoint) to prevent brute-force, with simple exponential backoff (e.g., increasing delays: 1s, 5s, 30s).
- **Suspicious Activity Detection**: Track failed attempts per IP/device; after 3 failures, apply throttling (delayed responses). Escalation to CAPTCHA (e.g., reCAPTCHA) or SMS (e.g., Twilio) is treated as future hooks—mocked in MVP (e.g., simulate with a flag returning a challenge response).
- **Additional Measures**: Input validation/sanitization to prevent injection; nonce for replay prevention; encrypted storage for sensitive data (though minimal here); audit logging of all requests/votes with timestamps/IPs. Handle fingerprint collisions by appending a unique suffix if hash conflicts.
- **Fallback**: If throttling thresholds are exceeded, block IP temporarily (e.g., 1 hour via Redis blacklist).

All mechanisms are configurable via environment variables for tuning, with CAPTCHA/SMS as optional extensions.

## 6. Scalability & Deployment
Recommended stack: Next.js for frontend (static SSR for performance), FastAPI for backend (async for high concurrency), PostgreSQL for database, Redis for caching/rate limiting (with in-memory fallback for dev). Deployment strategy: Containerize with Docker (separate images for frontend/backend); orchestrate with Docker Compose for local/dev or Kubernetes for production. Host on cloud (e.g., AWS/EC2 or Vercel for Next.js, Heroku/Fly.io for FastAPI). Use auto-scaling groups for backend based on CPU/load; database sharding by contestant if vote volume exceeds 1M/day. Load balancing via NGINX or cloud LB. Logging/Auditing: Integrate structured logging (e.g., FastAPI with Loguru) to centralized service like ELK Stack or CloudWatch; audit all votes and security events for compliance. Monitoring: Prometheus/Grafana for metrics, with alerts on high error rates or vote spikes.

Logging & Audit Fields Table:

| Event              | Data Logged                  | Retention | Purpose          |
|--------------------|------------------------------|-----------|------------------|
| Vote Submission   | device_token, ip, timestamp, result | 90 days  | Audit           |
| Rate Limit Trigger| ip, device_token, timestamp | 30 days  | Security        |
| CAPTCHA/SMS Attempt (Mocked) | ip, device_token, timestamp | 7 days   | Fraud detection |

## 7. Edge Cases & Failure Modes
- **Invalid Input**: Empty/malformed last_name → 400 with specific error; non-existent contestant → 400 "Contestant not found".
- **Vote Limits**: Device exceeds 3 total votes or duplicates per contestant → 400 "Limit reached"; handle fingerprint collisions by regenerating token with suffix.
- **Multiple Devices**: User switches devices → treated as new (no cross-device linking); but detect patterns (e.g., same IP, rapid votes) as suspicious → apply throttling.
- **API Abuse**: DDoS-like traffic → rate limiting triggers 429 with backoff; persistent abuse → IP blacklisting.
- **Failures**: Database downtime → backend returns 503, retry with exponential backoff; network issues → frontend shows retry button. Offline handling: No offline votes; require connectivity.
- **Other**: Timezone inconsistencies → store all timestamps in UTC; nonce reuse → 400 "Invalid nonce"; high-latency mocks → keep synchronous for simplicity.

## 8. Testing Strategy
Adopt a comprehensive strategy covering unit, integration, and end-to-end tests, with automatable verification criteria tied to rules enforcement.
- **Unit Tests**: Test individual components, e.g., fingerprint hashing function (input/output assertions), vote validation logic (mock database queries for limit checks), rate limiter middleware (simulate requests).
- **Integration Tests**: Use Pytest for backend (test API endpoints with mocked external services); Next.js testing library for frontend (form submission, error display). Cover data flows: e.g., full vote path from API to database insert.
- **End-to-End Tests**: Cypress or Playwright to simulate user journeys (vote submission, limit enforcement, throttling escalation).
- **Validation Coverage**: Ensure 80%+ code coverage; focus on security paths (e.g., fuzz testing for inputs, load testing for rate limits with Locust). Mock dependencies (e.g., Redis, external services) in CI/CD pipeline. Run tests in staged environments before production deployment.
- **Automatable Verification Criteria**:
  - Test that a device cannot vote for the same contestant twice (expect 400 on duplicate).
  - Test that total votes ≤ 3 per device (expect 400 on fourth attempt).
  - Test that invalid contestants are rejected (expect 400).
  - Test that suspicious IPs trigger 429 after thresholds (e.g., >5 requests/min).
  - Test nonce prevents replay (expect 400 on reused nonce).

## 9. Implementation Tasks for Agent
To facilitate deterministic execution by an Implementation Agent:
- Generate FastAPI endpoints based on /vote spec, including nonce validation and rate limiting middleware.
- Implement Redis-based device vote tracker with in-memory fallback if Redis not configured.
- Write simple Next.js frontend with text input, submit button, fingerprint generation (via library), nonce creation, and feedback message display.
- Set up PostgreSQL schema with CHECK constraints and triggers for vote limits.
- Add mocked hooks for CAPTCHA/SMS escalation (e.g., config flag to simulate responses).
- Integrate basic logging with the specified audit fields.
- Ensure all components are Dockerized for easy deployment.
