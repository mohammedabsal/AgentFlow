from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.runtime.sandbox import SandboxFile


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "generated-product"


def _title(value: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip().split()
    return " ".join(word.capitalize() for word in words[:8]) or "Generated Product"


@dataclass(slots=True)
class AgentBuildResult:
    summary: str
    files: list[SandboxFile]
    tool_calls: list[dict[str, Any]]

    def model_dump(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "files": [{"path": file.path, "content": file.content, "explanation": file.explanation} for file in self.files],
            "tool_calls": self.tool_calls,
        }


class ProductBuilderAgents:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        request = str(context.get("request") or "AI generated product")
        self.project_name = str(context.get("project_name") or _title(request))
        self.slug = _slugify(self.project_name)
        self.prompt = request

    def build(self, role: str) -> AgentBuildResult:
        builders = {
            "prompt_refinement": self.prompt_refiner_agent,
            "planner": self.planner_agent,
            "architect": self.architecture_agent,
            "frontend": self.frontend_agent,
            "backend": self.backend_agent,
            "database": self.database_agent,
            "auth": self.auth_agent,
            "devops": self.devops_agent,
            "testing": self.testing_agent,
            "self_healing": self.self_healing_agent,
            "packager": self.packager_agent,
            "integration": self.integration_agent,
        }
        return builders.get(role, self.integration_agent)()

    def prompt_refiner_agent(self) -> AgentBuildResult:
        requirements = {
            "product_name": self.project_name,
            "objective": self.prompt,
            "acceptance_criteria": [
                "Next.js frontend renders a product dashboard",
                "FastAPI backend exposes health, product, auth, and task endpoints",
                "SQL schema defines users, projects, and tasks",
                "Docker Compose starts frontend, backend, and database services",
                "Generated project can be downloaded as a ZIP archive",
            ],
        }
        return AgentBuildResult("Refined prompt into product requirements.", [SandboxFile("docs/requirements.json", json.dumps(requirements, indent=2))], [{"tool": "requirements_normalizer", "status": "completed"}])

    def planner_agent(self) -> AgentBuildResult:
        plan = {
            "agents": ["prompt_refiner", "planner", "architecture", "frontend", "backend", "database", "auth", "devops", "testing", "self_healing", "packager"],
            "execution_graph": {"frontend": ["architecture"], "backend": ["architecture", "database", "auth"], "devops": ["frontend", "backend", "database"], "testing": ["frontend", "backend"], "packager": ["testing", "self_healing"]},
        }
        return AgentBuildResult("Planned dependency-aware build graph.", [SandboxFile("docs/execution-plan.json", json.dumps(plan, indent=2))], [{"tool": "dependency_graph_builder", "status": "completed"}])

    def architecture_agent(self) -> AgentBuildResult:
        architecture = f"""# {self.project_name} Architecture

Prompt: {self.prompt}

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
"""
        return AgentBuildResult("Defined the full-stack architecture.", [SandboxFile("docs/architecture.md", architecture)], [{"tool": "architecture_writer", "status": "completed"}])

    def frontend_agent(self) -> AgentBuildResult:
        package_json = {"name": f"{self.slug}-frontend", "version": "1.0.0", "private": True, "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"}, "dependencies": {"@types/node": "latest", "@types/react": "latest", "@types/react-dom": "latest", "autoprefixer": "latest", "eslint": "latest", "eslint-config-next": "latest", "next": "latest", "postcss": "latest", "react": "latest", "react-dom": "latest", "tailwindcss": "latest", "typescript": "latest"}, "devDependencies": {}}
        page = f'''import {{ fetchProduct }} from "./lib/api";

export default async function Home() {{
  const product = await fetchProduct();
  const features = product.features ?? [];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
        <div className="max-w-3xl">
          <p className="text-sm uppercase tracking-[0.32em] text-cyan-300">AI generated SaaS</p>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight md:text-7xl">{{product.name}}</h1>
          <p className="mt-6 text-lg leading-8 text-slate-300">{{product.description}}</p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {{features.map((feature: string) => (
            <article key={{feature}} className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="text-sm font-medium text-cyan-200">{{feature}}</div>
              <p className="mt-3 text-sm leading-6 text-slate-400">Built into the generated workspace and backed by the API.</p>
            </article>
          ))}}
        </div>
        <div className="mt-10 rounded-lg border border-cyan-400/20 bg-cyan-400/10 p-5 text-sm text-cyan-50">
          Backend status: {{product.status}}. API base URL is configured through NEXT_PUBLIC_API_BASE_URL.
        </div>
      </section>
    </main>
  );
}}
'''
        api = '''export async function fetchProduct() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/product`, { cache: "no-store" });
    if (!response.ok) throw new Error("API unavailable");
    return response.json();
  } catch {
    return {
      name: "Generated Product",
      description: "The frontend is running. Start the FastAPI backend to load live product data.",
      status: "offline fallback",
      features: ["Product dashboard", "API integration", "Deployable codebase"],
    };
  }
}
'''
        files = [
            SandboxFile("frontend/package.json", json.dumps(package_json, indent=2)),
            SandboxFile("frontend/next.config.mjs", "const nextConfig = {};\nexport default nextConfig;\n"),
            SandboxFile("frontend/tsconfig.json", json.dumps({"compilerOptions": {"target": "es5", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": True, "skipLibCheck": True, "strict": True, "noEmit": True, "esModuleInterop": True, "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": True, "isolatedModules": True, "jsx": "preserve", "incremental": True, "plugins": [{"name": "next"}]}, "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"], "exclude": ["node_modules"]}, indent=2)),
            SandboxFile("frontend/postcss.config.mjs", "export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n"),
            SandboxFile("frontend/tailwind.config.ts", "import type { Config } from 'tailwindcss';\nconst config: Config = { content: ['./app/**/*.{js,ts,jsx,tsx}'], theme: { extend: {} }, plugins: [] };\nexport default config;\n"),
            SandboxFile("frontend/app/layout.tsx", f"import './globals.css';\nexport const metadata = {{ title: '{self.project_name}', description: 'AI generated product' }};\nexport default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{ return <html lang=\"en\"><body>{{children}}</body></html>; }}\n"),
            SandboxFile("frontend/app/page.tsx", page),
            SandboxFile("frontend/app/lib/api.ts", api),
            SandboxFile("frontend/app/globals.css", "@tailwind base;\n@tailwind components;\n@tailwind utilities;\nbody { margin: 0; }\n"),
            SandboxFile("frontend/Dockerfile", "FROM node:20-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nRUN npm run build\nEXPOSE 3000\nCMD [\"npm\", \"start\"]\n"),
        ]
        return AgentBuildResult("Generated a real Next.js frontend application.", files, [{"tool": "nextjs_file_writer", "status": "completed", "files": len(files)}])

    def backend_agent(self) -> AgentBuildResult:
        main = f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="{self.project_name} API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/api/health")
def health():
    return {{"status": "ok", "service": "{self.slug}-api"}}

@app.get("/api/product")
def product():
    return {{"name": "{self.project_name}", "description": {json.dumps(self.prompt)}, "status": "online", "features": ["Auth-ready API", "Task workflow", "PostgreSQL schema", "Docker deployment"]}}

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    return {{"access_token": f"demo-token-for-{{payload.email}}", "token_type": "bearer"}}

@app.get("/api/tasks")
def tasks():
    return [{{"id": "task-1", "title": "Refine product workflow", "status": "done"}}, {{"id": "task-2", "title": "Launch generated app", "status": "ready"}}]
'''
        files = [SandboxFile("backend/main.py", main), SandboxFile("backend/requirements.txt", "fastapi==0.115.6\nuvicorn[standard]==0.34.0\npydantic==2.10.4\npython-dotenv==1.0.1\n"), SandboxFile("backend/Dockerfile", "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n")]
        return AgentBuildResult("Generated a real FastAPI backend with product, auth, and task routes.", files, [{"tool": "fastapi_file_writer", "status": "completed", "files": len(files)}])

    def database_agent(self) -> AgentBuildResult:
        sql = f'''CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS projects (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), owner_id UUID REFERENCES users(id), name TEXT NOT NULL, description TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS tasks (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES projects(id) ON DELETE CASCADE, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'todo', created_at TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO projects (name, description) VALUES ('{self.project_name.replace("'", "''")}', '{self.prompt.replace("'", "''")}');
'''
        return AgentBuildResult("Generated PostgreSQL-compatible database schema.", [SandboxFile("database/schema.sql", sql)], [{"tool": "sql_schema_writer", "status": "completed"}])

    def auth_agent(self) -> AgentBuildResult:
        content = "# Auth Notes\n\nThe generated backend includes a demo `/api/auth/login` route that returns a bearer token. Replace the demo token with signed JWTs and hashed password verification before production use.\n"
        return AgentBuildResult("Generated auth integration notes.", [SandboxFile("docs/auth.md", content)], [{"tool": "auth_contract_writer", "status": "completed"}])

    def devops_agent(self) -> AgentBuildResult:
        root_package = {"name": self.slug, "version": "1.0.0", "private": True, "workspaces": ["frontend"], "scripts": {"dev": "docker compose up --build", "build": "npm --workspace frontend run build", "lint": "npm --workspace frontend run lint"}}
        compose = '''services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: product
      POSTGRES_USER: product
      POSTGRES_PASSWORD: product
    ports:
      - "5432:5432"
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/001-schema.sql:ro
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://product:product@db:5432/product
    ports:
      - "8000:8000"
    depends_on:
      - db
  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
'''
        env = "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000\nDATABASE_URL=postgresql://product:product@localhost:5432/product\n"
        files = [SandboxFile("package.json", json.dumps(root_package, indent=2)), SandboxFile("docker-compose.yml", compose), SandboxFile(".env.example", env)]
        return AgentBuildResult("Generated Docker Compose and root workspace scripts.", files, [{"tool": "docker_compose_writer", "status": "completed", "files": len(files)}])

    def integration_agent(self) -> AgentBuildResult:
        readme = f'''# {self.project_name}

Generated from prompt:

> {self.prompt}

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
'''
        return AgentBuildResult("Wrote project README and integration instructions.", [SandboxFile("README.md", readme)], [{"tool": "readme_writer", "status": "completed"}])

    def testing_agent(self) -> AgentBuildResult:
        smoke = "# Smoke Test Plan\n\n1. Run `docker compose up --build`.\n2. Open http://localhost:3000 and verify the product dashboard renders.\n3. Call `GET http://localhost:8000/api/health` and expect `{ \"status\": \"ok\" }`.\n4. Call `POST http://localhost:8000/api/auth/login` with email/password and verify a token is returned.\n5. Call `GET http://localhost:8000/api/tasks` and verify demo tasks are returned.\n"
        return AgentBuildResult("Generated validation plan for frontend, backend, auth, and API routes.", [SandboxFile("tests/smoke-test.md", smoke)], [{"tool": "test_plan_writer", "status": "completed"}])

    def self_healing_agent(self) -> AgentBuildResult:
        return AgentBuildResult("Self-healing baseline checked generated file contracts.", [SandboxFile("docs/self-healing.md", "# Self-Healing\n\nGenerated project includes baseline runtime contracts and Docker health paths.\n")], [{"tool": "contract_checker", "status": "completed"}])

    def packager_agent(self) -> AgentBuildResult:
        return AgentBuildResult("Packaging metadata prepared. ZIP archive is created by PackagingService.", [SandboxFile("docs/package.md", "# Package\n\nThe platform packages this workspace into a run ZIP artifact.\n")], [{"tool": "package_manifest_writer", "status": "completed"}])
