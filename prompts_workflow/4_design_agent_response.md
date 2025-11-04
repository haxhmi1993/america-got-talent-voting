# System Design: America's Got Talent Voting System

## 1. System Overview
This system provides a secure, web-based voting platform for "America's Got Talent," allowing users to vote for contestants by submitting their last name via a minimal frontend interface. The backend enforces strict voting rules—limiting each device to one vote per contestant and a maximum of three votes total—while incorporating fraud prevention through device fingerprinting, IP rate limiting, and escalating verification for suspicious activity. Votes are stored securely in a database, ensuring integrity and auditability, with the overall design prioritizing scalability for high-traffic events.

## 2. Architecture
The system follows a client-server architecture with a Next.js frontend for the user interface, a FastAPI backend for business logic and API handling, and a PostgreSQL database for persistent storage. The frontend interacts with the backend via RESTful APIs over HTTPS, sending vote requests with device fingerprints generated client-side (e.g., using a library like FingerprintJS). The backend validates inputs, checks vote limits using cached device tokens in Redis for performance, and persists valid votes to the database. Security layers include middleware for rate limiting (e.g., via FastAPI's built-in dependencies or SlowAPI) and integration with external services like Google reCAPTCHA for CAPTCHA or Twilio for SMS verification. Data flows unidirectionally: frontend to backend for votes, with backend querying the database and cache as needed. For scalability, the backend can be deployed behind a load balancer, with horizontal scaling of API instances.

Architecture Diagram Description (Textual Representation):
- **Frontend (Next.js)**: Handles UI rendering and client-side fingerprint generation → Sends API requests.
- **Backend (FastAPI)**: Receives requests → Validates (rate limit, fingerprint) → Queries/Updates Database & Cache → Responds.
- **Cache (Redis)**: Stores device tokens and vote counts for quick lookups.
- **Database (PostgreSQL)**: Stores contestants, votes, and device tokens.
- **External Services**: CAPTCHA/SMS providers for fraud escalation.
Interactions are synchronous for vote submission, with asynchronous logging for audits.

## 3. Data Models
The system uses relational data models in PostgreSQL, with entities designed for efficient querying and integrity constraints.

- **Contestant**: Represents a participant.
  - Fields: id (UUID, primary key), last_name (string, unique, indexed), created_at (timestamp).
  
- **DeviceToken**: Tracks unique devices via hashed fingerprints.
  - Fields: id (UUID, primary key), token (string, unique, hashed fingerprint), total_votes (integer, default 0), created_at (timestamp), last_activity (timestamp).
  
- **Vote**: Records each vote instance.
  - Fields: id (UUID, primary key), contestant_id (UUID, foreign key to Contestant), device_token_id (UUID, foreign key to DeviceToken), voted_at (timestamp).
  - Constraints: Unique composite index on (contestant_id, device_token_id) to prevent duplicate votes per device-contestant pair.

Relationships:
- One-to-Many: DeviceToken → Votes (a device can have multiple votes, up to 3 total).
- One-to-Many: Contestant → Votes (a contestant can receive multiple votes).
- Indexes: On Vote.voted_at for time-based queries; on DeviceToken.token for fast lookups.
Data flow: On vote submission, backend hashes the fingerprint to create/query DeviceToken, increments total_votes if under limit, and inserts Vote if no duplicate exists.

## 4. API Design
The backend exposes a single primary endpoint for voting, with additional health-check endpoints. All APIs use JSON payloads, require HTTPS, and include CORS headers for frontend integration.

- **POST /vote**
  - Parameters: Body { "last_name": string (required, min 2 chars, max 50 chars), "fingerprint": string (required, client-generated raw fingerprint) }.
  - Validation: Sanitize inputs (strip whitespace, lowercase last_name for matching); check contestant existence via database query; hash fingerprint (e.g., SHA-256) to generate token; enforce device limits (query DeviceToken for total_votes < 3 and no existing Vote for this contestant).
  - Responses:
    - 200 OK: { "status": "success", "message": "Vote recorded" }.
    - 400 Bad Request: { "status": "error", "message": "Invalid contestant name" or "Vote limit reached" }.
    - 429 Too Many Requests: { "status": "error", "message": "Rate limit exceeded; try CAPTCHA" } (with CAPTCHA challenge in response if escalated).
    - 500 Internal Server Error: Generic error for unexpected failures.
  - Constraints: Rate-limited by IP (e.g., 5 requests/min) and device token.

- **GET /health**: No params; returns 200 OK { "status": "healthy" } for monitoring.

Integration: Frontend collects fingerprint on load, submits on form submission; backend handles all validation synchronously.

## 5. Security and Fraud Prevention
Security emphasizes vote integrity through multi-layered defenses:
- **Device Fingerprinting**: Client generates fingerprint (e.g., via FingerprintJS, including browser/OS metrics); backend hashes it with salt (stored in env vars) to create a persistent token, stored in DeviceToken. This enforces per-device limits without user accounts.
- **IP-Based Rate Limiting**: Use middleware to limit requests per IP (e.g., 10/min globally, 3/min per endpoint) to prevent brute-force.
- **Suspicious Activity Detection**: Track failed attempts per IP/device; after 3 failures, throttle (delay responses); after 5, require CAPTCHA (integrate reCAPTCHA v3, validate token in request); for high-risk (e.g., VPN IPs or rapid multi-device attempts), escalate to SMS verification (send OTP via Twilio, require in subsequent request).
- **Additional Measures**: Input validation/sanitization to prevent injection; JWT or API keys for internal services if expanded; encrypted storage for sensitive data (though minimal here); audit logging of all requests/votes with timestamps/IPs.
- **Fallback**: If CAPTCHA fails repeatedly, block IP temporarily (e.g., 1 hour via Redis blacklist).

All mechanisms are configurable via environment variables for tuning.

## 6. Scalability & Deployment
Recommended stack: Next.js for frontend (static SSR for performance), FastAPI for backend (async for high concurrency), PostgreSQL for database, Redis for caching/rate limiting. Deployment strategy: Containerize with Docker (separate images for frontend/backend); orchestrate with Kubernetes or Docker Compose for local/dev. Host on cloud (e.g., AWS/EC2 or Vercel for Next.js, Heroku/Fly.io for FastAPI). Use auto-scaling groups for backend based on CPU/load; database sharding by contestant if vote volume exceeds 1M/day. Load balancing via NGINX or cloud LB. Logging/Auditing: Integrate structured logging (e.g., FastAPI with Loguru) to centralized service like ELK Stack or CloudWatch; audit all votes and security events for compliance. Monitoring: Prometheus/Grafana for metrics, with alerts on high error rates or vote spikes.

## 7. Edge Cases & Failure Modes
- **Invalid Input**: Empty/malformed last_name → 400 with specific error; non-existent contestant → 400 "Contestant not found".
- **Vote Limits**: Device exceeds 3 total votes or duplicates per contestant → 400 "Limit reached"; handle fingerprint collisions by regenerating if hash conflicts (rare).
- **Multiple Devices**: User switches devices → treated as new (no cross-device linking); but detect patterns (e.g., same IP, rapid votes) as suspicious → escalate to CAPTCHA/SMS.
- **API Abuse**: DDoS-like traffic → rate limiting triggers 429; persistent abuse → IP blacklisting.
- **Failures**: Database downtime → backend returns 503, retry with exponential backoff; network issues → frontend shows retry button. Offline handling: No offline votes; require connectivity.
- **Other**: Timezone inconsistencies → store all timestamps in UTC; high-latency CAPTCHA/SMS → asynchronous verification if needed, but keep synchronous for simplicity.

## 8. Testing Strategy
Adopt a comprehensive strategy covering unit, integration, and end-to-end tests.
- **Unit Tests**: Test individual components, e.g., fingerprint hashing function (input/output assertions), vote validation logic (mock database queries for limit checks), rate limiter middleware (simulate requests).
- **Integration Tests**: Use Pytest for backend (test API endpoints with mocked external services like CAPTCHA); Next.js testing library for frontend (form submission, error display). Cover data flows: e.g., full vote path from API to database insert.
- **End-to-End Tests**: Cypress or Playwright to simulate user journeys (vote submission, limit enforcement, CAPTCHA escalation).
- **Validation Coverage**: Ensure 80%+ code coverage; focus on security paths (e.g., fuzz testing for inputs, load testing for rate limits with Locust). Mock dependencies (e.g., Redis, Twilio) in CI/CD pipeline. Run tests in staged environments before production deployment.
