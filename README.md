# America's Got Talent (AGT) Voting System POC

A proof-of-concept voting system designed for high-volume, secure voting with device-based rate limiting and fraud prevention.

## 🎯 Features

- **Device-based Vote Limiting**: Each device can vote up to 3 times across different contestants
- **Duplicate Vote Prevention**: One vote per contestant per device
- **Rate Limiting**: IP-based rate limiting (configurable, default 5 req/min)
- **Nonce Protection**: Prevents replay attacks with one-time nonces
- **Fingerprint-based Device Tracking**: Uses device fingerprinting (hashed & salted)
- **Redis Cache**: With automatic in-memory fallback
- **Atomic Vote Recording**: Transaction-based consistency
- **Health & Metrics**: `/health` and `/metrics` endpoints
- **Escalation Hooks**: Mock CAPTCHA/SMS escalation support

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL)
- **FastAPI** - Async Python web framework
- **PostgreSQL** - Primary data store
- **Redis** - Caching and rate limiting (with in-memory fallback)
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations
- **Prometheus** - Metrics collection

### Frontend (Next.js)
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **FingerprintJS** - Device fingerprinting
- **CSS Modules** - Scoped styling

## 📋 Prerequisites

- **Docker** & **Docker Compose** (recommended)
- OR
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis 7+** (optional)

## 🚀 Quick Start with Docker Compose

### 1. Clone and Setup

```bash
cd voting_system
cp .env.example .env
# Edit .env with your configuration if needed
```

### 2. Start All Services

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL on port 5432
- Start Redis on port 6379
- Run database migrations
- Seed sample contestants
- Start backend API on http://localhost:8000
- Start frontend on http://localhost:3000

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

### 4. Test Voting

1. Open http://localhost:3000
2. Enter a contestant's last name (e.g., "Smith", "Johnson", "Williams")
3. Click "Submit Vote"
4. Try voting for different contestants (up to 3 times)

## 🧪 Running Tests

### Backend Tests

```bash
# Inside backend container
docker-compose exec backend pytest -v

# Or locally
cd backend
pytest -v
```

### Test Coverage

```bash
cd backend
pytest --cov=. --cov-report=html
# Open htmlcov/index.html
```

## 📁 Project Structure

```
voting_system/
├── backend/
│   ├── alembic/                 # Database migrations
│   │   └── versions/
│   ├── routes/                  # API endpoints
│   │   ├── vote.py             # POST /api/vote
│   │   ├── health.py           # GET /health
│   │   └── metrics.py          # GET /metrics
│   ├── services/                # Business logic
│   │   ├── cache.py            # Redis/in-memory cache
│   │   └── db.py               # Database operations
│   ├── utils/                   # Utilities
│   │   ├── security.py         # Hashing, validation
│   │   └── rate_limiter.py     # Rate limiting logic
│   ├── tests/                   # Unit & integration tests
│   ├── models.py                # SQLAlchemy models
│   ├── config.py                # Configuration
│   ├── database.py              # DB connection
│   ├── main.py                  # FastAPI app
│   ├── seed.py                  # DB seeding script
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/                   # Next.js pages
│   │   ├── index.tsx           # Home page
│   │   ├── _app.tsx
│   │   └── _document.tsx
│   ├── components/              # React components
│   │   └── VoteForm.tsx        # Vote submission form
│   ├── styles/                  # CSS modules
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://voting_user:voting_pass@postgres:5432/voting_db

# Redis (optional - will use in-memory if not set)
REDIS_URL=redis://redis:6379

# Security
FINGERPRINT_SALT=your-secret-salt-here

# Rate Limiting
IP_RATE_LIMIT=5          # requests per window
IP_RATE_WINDOW=60        # seconds

# Nonce TTL
NONCE_TTL=300            # 5 minutes

# Escalation
ENABLE_ESCALATION=false  # set to true for CAPTCHA challenges
```

## 🗃️ Database Schema

### Contestants
- `id` (UUID, PK)
- `first_name` (String)
- `last_name` (String)
- `last_name_normalized` (String, indexed)
- `created_at` (Timestamp)

### DeviceTokens
- `id` (UUID, PK)
- `token` (String, unique, indexed) - SHA-256 hash of fingerprint
- `total_votes` (Integer, CHECK <= 3)
- `created_at`, `updated_at` (Timestamps)

### Votes
- `id` (UUID, PK)
- `contestant_id` (UUID, FK)
- `device_token_id` (UUID, FK)
- `voted_at` (Timestamp, indexed)
- UNIQUE constraint on (contestant_id, device_token_id)

## 🔒 Security Features

1. **Fingerprint Hashing**: All device fingerprints are hashed with a secret salt
2. **Nonce Validation**: Each request requires a unique nonce (5-minute TTL)
3. **Rate Limiting**: IP-based rate limiting with configurable thresholds
4. **Atomic Transactions**: Vote recording uses database transactions with row locking
5. **Input Validation**: Last names validated against whitelist patterns
6. **IP Masking**: Client IPs are masked in logs for privacy

## 📊 API Endpoints

### POST /api/vote

Submit a vote for a contestant.

**Request:**
```json
{
  "last_name": "Smith",
  "fingerprint": "device-fingerprint-string",
  "nonce": "unique-nonce-string"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Vote recorded successfully"
}
```

**Response (Rate Limited):**
```json
{
  "status": "challenge",
  "message": "Too many requests. Please complete verification.",
  "type": "captcha"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "agt-voting-system",
  "version": "1.0.0"
}
```

### GET /metrics

Prometheus metrics endpoint.

## 🧩 Sample Contestants

The database is seeded with 10 sample contestants:
- Smith, Johnson, Williams, Brown, Jones
- Garcia, Martinez, Rodriguez, Wilson, Anderson

## 🛠️ Development

### Local Development (Without Docker)

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/voting_db"
export FINGERPRINT_SALT="dev-salt"

# Run migrations
alembic upgrade head

# Seed database
python seed.py

# Start server
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment variable
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart services
docker-compose restart postgres backend
```

### Redis Connection Issues

The system automatically falls back to in-memory cache if Redis is unavailable.

### Port Conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change host port
  frontend:
    ports:
      - "3001:3000"  # Change host port
```

## 📈 Scalability Considerations

This POC includes design patterns for scaling:

1. **Stateless Backend**: All state in PostgreSQL/Redis
2. **Cache Layer**: Redis reduces database load
3. **Horizontal Scaling**: Backend can run multiple instances behind load balancer
4. **Connection Pooling**: SQLAlchemy manages DB connections efficiently
5. **Async I/O**: FastAPI async endpoints for high concurrency

## 🔄 Migration Guide

### Adding New Migrations

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description"

# Review migration in alembic/versions/

# Apply migration
alembic upgrade head
```

## 📝 Testing Strategy

- **Unit Tests**: Test individual functions (utils, cache)
- **Integration Tests**: Test API endpoints with in-memory SQLite
- **Concurrency Tests**: Test race conditions in vote recording
- **Rate Limit Tests**: Verify rate limiting behavior

## 🚦 Production Checklist

Before deploying to production:

- [ ] Change `FINGERPRINT_SALT` to a strong random value
- [ ] Use strong PostgreSQL credentials
- [ ] Enable Redis authentication
- [ ] Configure proper CORS origins in backend
- [ ] Set `ENABLE_ESCALATION=true` for CAPTCHA
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper logging and monitoring
- [ ] Set up database backups
- [ ] Configure rate limits based on expected traffic
- [ ] Review and harden security headers

## 📄 License

This is a proof-of-concept project for demonstration purposes.

## 🤝 Contributing

This is a POC project. For production use, consider:
- Adding authentication/authorization
- Implementing actual CAPTCHA integration
- Adding SMS verification
- Enhanced monitoring and alerting
- Load testing and performance optimization
- Security audit

## 📞 Support

For issues or questions, please check the logs:

```bash
docker-compose logs backend
docker-compose logs frontend
```
