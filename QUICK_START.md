# AgentFlow Quick Start Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker
- Redis
- PostgreSQL (or SQLite for local dev)

## Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

### 3. Services

```bash
# Start Redis (if not using Docker)
redis-server

# Start PostgreSQL (if not using Docker)
# or use the included docker-compose

docker-compose up -d
```

## Configuration

### Environment Variables

**Backend** (`.env` in `/backend`):

```env
# API Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
DEBUG=true

# LLM Configuration
LLM_PROVIDER=openai  # Options: openai, gemini, anthropic, groq
LLM_MODEL=gpt-4-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4000

# API Keys (set these)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agentflow
# Or for SQLite: sqlite:///./agentflow.db

# Redis
REDIS_URL=redis://localhost:6379

# Workspace Configuration
WORKSPACE_BASE_PATH=/tmp/agentflow-workspaces
WORKSPACE_DOCKER_IMAGE=ubuntu:22.04

# Observability
SENTRY_DSN=
OMIUM_API_KEY=
```

**Frontend** (`.env.local` in `/frontend`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=AgentFlow
```

## Basic Usage

### 1. Start the System

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis (if needed)
redis-server
```

### 2. Open in Browser

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 3. Generate Your First Project

1. Navigate to `/builder` page
2. Enter project name: "Todo App"
3. Enter description:
   ```
   Build a modern todo application with:
   - React frontend with TypeScript and Tailwind CSS
   - FastAPI Python backend with PostgreSQL
   - User authentication with JWT
   - Real-time updates
   - Responsive design
   ```
4. Click "Generate Project"
5. Watch the agents work in real-time
6. Download the complete project when done

## API Usage Examples

### Start Workflow

```bash
curl -X POST http://localhost:8000/api/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "My App",
    "user_prompt": "Build a weather app with React and Node.js",
    "enable_self_healing": true
  }'

# Response:
# {
#   "execution_id": "uuid",
#   "status": "initialized",
#   "websocket_url": "/api/orchestration/ws/uuid"
# }
```

### Get Status

```bash
curl http://localhost:8000/api/orchestration/status/{execution_id}

# Response:
# {
#   "execution_id": "uuid",
#   "status": "running",
#   "current_task": "frontend_generation",
#   "completed_tasks": ["prompt_refinement", "research", "planning"],
#   "progress": "3/11",
#   "logs": [...]
# }
```

### WebSocket Connection (JavaScript)

```javascript
const executionId = 'your-execution-id';
const ws = new WebSocket(`ws://localhost:8000/api/orchestration/ws/${executionId}`);

ws.onopen = () => {
  console.log('Connected to execution stream');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'log':
      console.log(`[${message.metadata.source}] ${message.content}`);
      break;
    case 'artifact':
      console.log(`Generated: ${message.metadata.path}`);
      break;
    case 'progress':
      console.log(`Progress: ${message.metadata.completed}/${message.metadata.total}`);
      break;
    case 'complete':
      console.log('Execution complete!');
      break;
    case 'error':
      console.error(`Error: ${message.content}`);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### List Artifacts

```bash
curl http://localhost:8000/api/orchestration/artifacts/{execution_id}

# Response:
# [
#   {
#     "artifact_id": "uuid",
#     "path": "frontend/src/App.tsx",
#     "language": "typescript",
#     "generated_by": "frontend",
#     "content": "..."
#   },
#   ...
# ]
```

### Download Project

```bash
# Get all artifacts and save to files
curl http://localhost:8000/api/orchestration/artifacts/{execution_id} \
  | jq -r '.[] | "\(.path) \(.content)"' > artifacts.txt

# Parse and save files
mkdir -p project
# ... parse and save each artifact to its path
```

## Project Structure

After generation, projects include:

```
generated-project/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   └── database.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── database/
│   ├── schema.sql
│   └── migrations/
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── README.md
├── DEPLOYMENT.md
└── .env.example
```

## Troubleshooting

### WebSocket Connection Issues

**Problem**: WebSocket connection fails
**Solution**: 
- Check CORS settings in backend
- Verify WebSocket URL is correct
- Check firewall rules

### Agent Execution Failures

**Problem**: Agents fail during execution
**Solution**:
- Check LLM API key is valid
- Review logs for specific errors
- Check self-healing loop output
- Increase token budget if needed

### Workspace Not Creating

**Problem**: Docker workspace creation fails
**Solution**:
- Verify Docker is running
- Check disk space
- Review Docker configuration
- Check workspace path permissions

### Database Connection Issues

**Problem**: Database connection error
**Solution**:
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Run migrations: `alembic upgrade head`
- Check database credentials

## Performance Tuning

### For Development
- Reduce `LLM_MAX_TOKENS` for faster testing
- Use local models when possible
- Disable some self-healing iterations

### For Production
- Use high-performance LLM models
- Enable Redis caching
- Use PostgreSQL (not SQLite)
- Enable Kubernetes scaling
- Configure proper logging and monitoring

## Next Steps

1. **Customize Agent Behavior** - Edit agent prompts in `/backend/app/agents/multi_agent_system.py`
2. **Add Custom Tools** - Extend agent capabilities in `/backend/app/tools/`
3. **Configure LLM Models** - Update model selection in `config.py`
4. **Set Up Monitoring** - Configure Sentry and Omnium SDK
5. **Deploy to Production** - Use provided Docker compose or K8s configs

## Support & Documentation

- **API Docs**: http://localhost:8000/docs
- **Architecture**: See `ARCHITECTURE_UPGRADED.md`
- **Issues**: Check GitHub issues
- **Contributing**: See `CONTRIBUTING.md`

## License

MIT - See LICENSE file
