# Smoke Product Architecture

Prompt: Build a small CRM

## System
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, SQL-ready repository layout
- Database: PostgreSQL-compatible SQL schema
- Auth: token-based demo auth flow with clear extension points
- DevOps: Dockerfiles and docker-compose for local deployment

## Data Flow
Frontend calls FastAPI through `NEXT_PUBLIC_API_BASE_URL`. The backend exposes
health, product metadata, login, and tasks endpoints. SQL schema lives in
`database/schema.sql` and can be loaded into PostgreSQL.
