# Deployment Guide

This guide covers deploying the Data Contract Engine to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Render.com Deployment](#rendercom-deployment)
- [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Git
- A cloud hosting account (Render, Streamlit Cloud, etc.)

## Local Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/data-contract-engine.git
cd data-contract-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL
docker-compose up -d

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd frontend
streamlit run streamlit_app.py
```

### Access Points

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501
- **Database**: localhost:5432
- **pgAdmin**: http://localhost:5050 (admin@dce.local / admin)

## Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker build -t data-contract-engine .

# Run the container
docker run -d \
  --name dce-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e LOG_LEVEL=INFO \
  data-contract-engine
```

### Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Render.com Deployment

Render.com offers free hosting for web services and PostgreSQL databases.

### Deploy PostgreSQL

1. Create Render account at [render.com](https://render.com)
2. Go to Dashboard → New → PostgreSQL
3. Configure:
   - Name: `data-contract-db`
   - Database: `dce_db`
   - User: `dce_user`
   - Region: Choose nearest region
   - Plan: Free (9GB limit)
4. Click "Create Database"
5. Copy the internal connection string

**Connection String Format**:
```
postgresql://dce_user:password@dce-db-host:5432/dce_db
```

### Deploy Backend

1. Go to Dashboard → New → Web Service
2. Connect your GitHub repository
3. Configure:
   - Name: `data-contract-api`
   - Environment: Docker
   - Build Command: (leave empty for Docker)
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `DATABASE_URL`: Paste your PostgreSQL connection string
   - `LOG_LEVEL`: `INFO`
5. Click "Deploy Web Service"

**Your API will be available at**: `https://data-contract-api.onrender.com`

### Run Migrations on Render

After deployment, run migrations:

1. Go to your web service
2. Click "Shell" (SSH)
3. Run:
```bash
alembic upgrade head
```

Alternatively, add migrations to your `Dockerfile`:

```dockerfile
RUN alembic upgrade head
```

## Streamlit Cloud Deployment

Streamlit Cloud offers free hosting for Streamlit apps.

### Deploy Frontend

1. Create Streamlit account at [share.streamlit.io](https://share.streamlit.io)
2. Go to "New app"
3. Configure:
   - Repository: Select your GitHub repo
   - Main file path: `frontend/streamlit_app.py`
4. Add Secrets:
   - `API_BASE_URL`: Your Render API URL (e.g., `https://data-contract-api.onrender.com/api/v1`)
5. Click "Deploy"

**Your app will be available at**: `https://yourapp.streamlit.app`

### Streamlit Configuration

The frontend uses `.streamlit/config.toml` for configuration:

```toml
[theme]
primaryColor = "#FF6B6B"

[server]
port = 8501
headless = true

[browser]
gatherUsageStats = false
```

## AWS Deployment

### ECR (Elastic Container Registry)

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t data-contract-engine .
docker tag data-contract-engine:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/data-contract-engine:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/data-contract-engine:latest
```

### ECS (Elastic Container Service)

1. Create ECS cluster
2. Create task definition:
   - Image: Your ECR image
   - Environment variables: DATABASE_URL, LOG_LEVEL
3. Create service
4. Configure load balancer (ALB)

### RDS PostgreSQL

1. Create PostgreSQL instance (free tier: t3.micro)
2. Configure security groups
3. Update `DATABASE_URL` in ECS task definition

## DigitalOcean Deployment

### App Platform

1. Create DigitalOcean account
2. Go to Apps → Create App
3. Select GitHub repository
4. Configure:
   - Build: Dockerfile
   - Environment: Python 3.11
   - Services: Backend (HTTP on port 8000)
5. Add database (Managed PostgreSQL)
6. Deploy

### Environment Variables

Add these in App Settings:
```
DATABASE_URL=postgresql://douser:password@dbhost:25060/defaultdb
LOG_LEVEL=INFO
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|-----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG`, `WARNING`, `ERROR` |

### Optional Variables

| Variable | Description | Default |
|-----------|-------------|----------|
| `API_V1_PREFIX` | API version prefix | `/api/v1` |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` |
| `PROJECT_NAME` | Application name | `Data Contract Engine` |
| `VERSION` | Application version | `1.0.0` |

### .env.example

```bash
# Database
DATABASE_URL=postgresql://dce_user:dce_password@localhost:5432/dce_db

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=Data Contract Engine
VERSION=1.0.0

# CORS
CORS_ORIGINS=["http://localhost:8501", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
```

## Database Migrations

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Apply specific migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# View migration history
alembic history

# View current version
alembic current
```

### Creating New Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Edit the migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

## Monitoring

### Health Check

```bash
curl https://your-api.com/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Logs

**Render**:
- Go to Dashboard → Your Service → Logs

**Streamlit Cloud**:
- Go to App → Logs

**Docker**:
```bash
docker logs -f data-contract-engine
```

### Metrics

Access metrics dashboard:
- API: `/api/v1/metrics/summary`
- UI: Streamlit Dashboard page

## Performance Tuning

### Database

**Connection Pooling**:
```python
# In app/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

**Indexes**:
Already configured in database models. Add custom indexes if needed:
```python
Index("idx_my_index", Contract.name, Contract.domain)
```

### API

**Async Workers**:
Use Gunicorn with uvicorn workers:
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Caching (Future)

Add Redis for caching:
```python
# Future implementation
from redis import Redis
cache = Redis(host='redis', port=6379)
```

## Security

### HTTPS

Always use HTTPS in production:
- Render: Automatic HTTPS
- Streamlit Cloud: Automatic HTTPS
- AWS: Use ALB with ACM certificate

### Secrets Management

**Never commit secrets to Git!**

Use platform-specific secrets:
- Render: Environment variables in dashboard
- Streamlit Cloud: Secrets in app settings
- AWS: Secrets Manager or Parameter Store

### API Keys (Future)

Implement API key authentication:
```python
# In app/main.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

## Troubleshooting

### Database Connection Issues

**Error**: `could not connect to server`

**Solutions**:
1. Check `DATABASE_URL` is correct
2. Verify database is running
3. Check firewall/security groups allow connection
4. Verify user permissions

### Migration Failures

**Error**: `Target database is not up to date`

**Solutions**:
```bash
# Check current version
alembic current

# Check history
alembic history

# Force upgrade (use carefully)
alembic stamp head
```

### CORS Errors

**Error**: `CORS policy blocked request`

**Solutions**:
1. Add frontend URL to `CORS_ORIGINS`
2. Check frontend uses correct `API_BASE_URL`
3. Verify both API and frontend use HTTPS

### Out of Memory

**Error**: Container OOM killed

**Solutions**:
1. Increase container memory limit
2. Reduce chunk size in batch processor
3. Add pagination to queries
4. Implement caching

### Slow Performance

**Symptoms**: Slow validation, high latency

**Solutions**:
1. Check database query performance with `EXPLAIN ANALYZE`
2. Add missing indexes
3. Increase connection pool size
4. Use read replicas for metrics queries
5. Enable caching

## Backup and Recovery

### PostgreSQL Backup

```bash
# Backup
pg_dump -h host -U user -d dbname > backup.sql

# Restore
psql -h host -U user -d dbname < backup.sql
```

### Render Backup

Render automatically backs up PostgreSQL daily. Access backups:
- Dashboard → PostgreSQL → Backups

### Streamlit Cloud State

Streamlit Cloud doesn't persist data. Use external database.

## Scaling

### Horizontal Scaling

1. Add load balancer (ALB, NGINX)
2. Deploy multiple API instances
3. Configure session storage (Redis)
4. Enable sticky sessions if needed

### Database Scaling

1. Add read replicas
2. Use connection pooling
3. Implement query caching
4. Optimize queries with EXPLAIN ANALYZE

## Cost Optimization

### Free Tier Limits

**Render Free Tier**:
- 512 MB RAM
- 0.1 CPU
- 750 hours/month
- PostgreSQL Free: 9GB storage

**Streamlit Cloud Free**:
- Limited resources
- Community support

### Cost Optimization Tips

1. Use free tiers for development
2. Monitor resource usage
3. Implement caching to reduce database load
4. Archive old validation results
5. Use read replicas for read-heavy workloads

---

**Document Version**: 1.0
**Last Updated**: January 12, 2026
