from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Smoke Product API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "smoke-product-api"}

@app.get("/api/product")
def product():
    return {"name": "Smoke Product", "description": "Build a small CRM", "status": "online", "features": ["Auth-ready API", "Task workflow", "PostgreSQL schema", "Docker deployment"]}

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    return {"access_token": f"demo-token-for-{payload.email}", "token_type": "bearer"}

@app.get("/api/tasks")
def tasks():
    return [{"id": "task-1", "title": "Refine product workflow", "status": "done"}, {"id": "task-2", "title": "Launch generated app", "status": "ready"}]
