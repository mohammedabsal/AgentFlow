# Smoke Product

Generated from prompt:

> Build a small CRM

## Run Locally

```bash
docker compose up --build
```

Frontend: http://localhost:3000
Backend health: http://localhost:8000/api/health

## Structure

- `frontend/` Next.js product UI
- `backend/` FastAPI product API
- `database/schema.sql` PostgreSQL schema
- `docker-compose.yml` full local stack
