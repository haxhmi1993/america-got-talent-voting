# Quick Reference Guide

## 🚀 Getting Started

### Option 1: Automatic Start
```bash
./start.sh
```

### Option 2: Manual Start
```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build
```

## 📍 URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | Service health |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |

## 🗳️ Sample Contestants

Vote using these last names:
- Smith
- Johnson
- Williams
- Brown
- Jones
- Garcia
- Martinez
- Rodriguez
- Wilson
- Anderson

## 📝 Common Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Database Operations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database
docker-compose exec backend python seed.py

# Connect to database
docker-compose exec postgres psql -U voting_user -d voting_db
```

### Testing
```bash
# Run all backend tests
docker-compose exec backend pytest -v

# Run specific test file
docker-compose exec backend pytest tests/test_vote_endpoint.py -v

# Run with coverage
docker-compose exec backend pytest --cov=. --cov-report=html
```

### Development
```bash
# Backend shell
docker-compose exec backend sh

# Frontend shell
docker-compose exec frontend sh

# Python shell with app context
docker-compose exec backend python
```

## 🧪 Testing the Vote Flow

### Using the Frontend
1. Go to http://localhost:3000
2. Enter a last name (e.g., "Smith")
3. Click "Submit Vote"
4. See the success message

### Using curl
```bash
# Submit a vote
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{
    "last_name": "Smith",
    "fingerprint": "test-fingerprint-123",
    "nonce": "test-nonce-'$(date +%s)'"
  }'
```

### Testing Vote Limits
```bash
# Vote for 3 different contestants (should work)
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"last_name": "Smith", "fingerprint": "device1", "nonce": "n1"}'

curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"last_name": "Johnson", "fingerprint": "device1", "nonce": "n2"}'

curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"last_name": "Williams", "fingerprint": "device1", "nonce": "n3"}'

# Try to vote for 4th contestant (should fail with 403)
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"last_name": "Brown", "fingerprint": "device1", "nonce": "n4"}'
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://voting_user:voting_pass@postgres:5432/voting_db

# Redis (optional)
REDIS_URL=redis://redis:6379

# Security - CHANGE IN PRODUCTION!
FINGERPRINT_SALT=your-secret-salt-here

# Rate Limiting
IP_RATE_LIMIT=5        # requests per window
IP_RATE_WINDOW=60      # seconds

# Nonce TTL
NONCE_TTL=300          # 5 minutes

# Escalation
ENABLE_ESCALATION=false
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check if database is ready
docker-compose ps postgres

# Restart backend
docker-compose restart backend
```

### Frontend can't connect to backend
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check environment variable
docker-compose exec frontend env | grep API_URL
```

### Database connection errors
```bash
# Check PostgreSQL
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up --build
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Or kill the process
kill -9 $(lsof -t -i:8000)
```

## 📊 Monitoring

### Check Health
```bash
curl http://localhost:8000/health
```

### View Metrics
```bash
curl http://localhost:8000/metrics
```

### Database Queries
```bash
docker-compose exec postgres psql -U voting_user -d voting_db -c "
SELECT 
  c.last_name,
  COUNT(v.id) as total_votes
FROM contestants c
LEFT JOIN votes v ON c.id = v.contestant_id
GROUP BY c.id, c.last_name
ORDER BY total_votes DESC;
"
```

## 🔒 Security Notes

### For Development
- Default credentials are okay
- Use HTTP (not HTTPS)
- CORS allows all origins

### For Production
1. Change `FINGERPRINT_SALT` to random string
2. Use strong database passwords
3. Enable Redis authentication
4. Configure CORS for specific domain
5. Enable SSL/TLS
6. Set `ENABLE_ESCALATION=true`
7. Use secrets manager for credentials

## 📈 Performance Tips

### Database
- Monitor slow queries in PostgreSQL logs
- Add indexes for frequently queried fields
- Consider read replicas for scaling

### Backend
- Scale horizontally: `docker-compose up -d --scale backend=3`
- Use load balancer (nginx, HAProxy)
- Monitor memory usage

### Redis
- Enable persistence for production
- Monitor memory usage
- Consider Redis Cluster for HA

## 🆘 Getting Help

### View Documentation
- Main README: `README.md`
- Implementation Details: `IMPLEMENTATION_TRANSCRIPT.md`
- API Docs: http://localhost:8000/docs

### Debug Mode
```bash
# Enable verbose logging
docker-compose up

# Watch logs in real-time
docker-compose logs -f backend | grep ERROR
```

## ✅ Pre-Production Checklist

- [ ] Change FINGERPRINT_SALT
- [ ] Update database credentials
- [ ] Configure CORS for production domain
- [ ] Enable Redis authentication
- [ ] Set up SSL/TLS
- [ ] Configure monitoring (Grafana/DataDog)
- [ ] Set up database backups
- [ ] Load test the system
- [ ] Security audit
- [ ] Review rate limits
