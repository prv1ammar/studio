# 🚀 Tyboo Studio v1.0 - Deployment Guide

Welcome to the production-ready deployment guide for Tyboo Studio. This guide helps you spin up the entire platform (Frontend, Backend, Redis, and Postgres) using Docker.

## 📋 Prerequisites
- **Docker** & **Docker Compose** installed.
- **Git** (to clone the repository).
- 4GB+ RAM recommended.

## ⚡ Quick Start (Production-like)

To deploy everything with a single command:

```bash
# On Linux/macOS
chmod +x deploy.sh
./deploy.sh

# On Windows (Manual)
docker-compose up -d --build
```

### Accessing the Platform
- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🐳 Container Architecture
The platform is orchestrated into 5 main containers:
1. `studio-frontend`: Nginx serving the React SPA.
2. `studio-api`: FastAPI hub handling requests and node logic.
3. `studio-worker`: ARQ worker processing long-running automation jobs.
4. `studio-postgres`: Persistent storage for workflows, users, and usage records.
5. `studio-redis`: Distributed cache and message broker for execution updates.

## 🛠️ Configuration
You can customize the deployment by editing the `environment` section in `docker-compose.yml` or creating a `.env` file in the root.

Important variables:
- `SECRET_KEY`: Used for JWT signing (Replace in real production!).
- `ENCRYPTION_KEY`: Used to encrypt sensitive node credentials in DB.
- `DATABASE_URL`: Connection string for Postgres.

## 📊 Maintenance & Logs
- **View Logs**: `docker-compose logs -f`
- **Restart All**: `docker-compose restart`
- **Clean Shutdown**: `docker-compose down -v` (Internal volumes will be deleted!)

---
**Build with ❤️ by Tyboo Team.**
