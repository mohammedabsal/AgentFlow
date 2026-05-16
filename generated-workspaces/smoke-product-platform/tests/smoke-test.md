# Smoke Test Plan

1. Run `docker compose up --build`.
2. Open http://localhost:3000 and verify the product dashboard renders.
3. Call `GET http://localhost:8000/api/health` and expect `{ "status": "ok" }`.
4. Call `POST http://localhost:8000/api/auth/login` with email/password and verify a token is returned.
5. Call `GET http://localhost:8000/api/tasks` and verify demo tasks are returned.
