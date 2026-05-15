# AgentFlow: Lovable-Style Autonomous AI Engineering Platform

## Overview

AgentFlow is a production-ready autonomous multi-agent AI software engineering platform inspired by Lovable, Devin, and Cursor. It transforms a single user prompt into a fully-functional, tested, and deployable full-stack application with minimal human intervention.

## Architecture

### Core Components

#### 1. **Multi-Agent Orchestration System**
- **11 Specialized Agents** working in coordinated phases:
  - **Prompt Refiner** - Clarifies user intent into structured requirements
  - **Research Agent** - Analyzes tech landscape and best practices
  - **Planner** - Decomposes work into executable tasks with dependencies
  - **Architecture Agent** - Designs system structure and schemas
  - **Frontend Agent** - Generates React/Next.js UI code
  - **Backend Agent** - Generates FastAPI server code
  - **Database Agent** - Designs PostgreSQL schemas and queries
  - **API Agent** - Designs REST/GraphQL APIs
  - **DevOps Agent** - Creates Docker/K8s configs
  - **Testing Agent** - Generates comprehensive test suites
  - **Self-Healing Agent** - Analyzes and fixes execution errors

#### 2. **Orchestration Engine** (LangGraph-inspired)
- Async task scheduling with dependency tracking
- Parallel agent execution where possible
- Real-time state management
- Automatic error recovery
- WebSocket streaming for live updates

#### 3. **Workspace Execution System**
- Docker-based sandboxed workspaces
- Real file creation and manipulation
- Actual code execution (install, build, test)
- Log capture and error analysis
- Automatic cleanup

#### 4. **Self-Healing Loop**
- Captures execution failures
- Analyzes root causes
- Generates targeted fixes
- Applies patches automatically
- Retries with improved code

#### 5. **Real-Time Streaming**
- WebSocket connections for live updates
- Agent status monitoring
- Code generation streaming
- Log streaming
- Error notifications

#### 6. **Lovable-Style Frontend**
- Dark modern UI with smooth animations
- Left workspace sidebar with file tree
- Chat-based generation interface
- Live code preview panel
- Execution timeline and logs
- Agent status dashboard
- Real-time progress tracking

## Execution Workflow

```
User Prompt
    ↓
[Prompt Refiner] → Refined Requirements
    ↓
[Research Agent] → Tech Recommendations
    ↓
[Planner] → Execution Plan with Dependencies
    ↓
[Architect] → System Design & Schema
    ↓
┌─────────────────────────────────────────┐
│  PARALLEL GENERATION PHASE               │
│  ├─ [Frontend Agent]                    │
│  ├─ [Backend Agent]                     │
│  ├─ [Database Agent]                    │
│  ├─ [API Agent]                         │
│  └─ [DevOps Agent]                      │
└─────────────────────────────────────────┘
    ↓
[Testing Agent] → Test Suite
    ↓
WORKSPACE EXECUTION
├─ Create workspace
├─ Write files
├─ Install dependencies
├─ Build project
├─ Run tests
└─ Capture output
    ↓
ERROR DETECTED?
├─ YES → [Self-Healing Agent] → Fixes → Re-execute
└─ NO → COMPLETE
    ↓
Downloadable Project
```

## Key Features

### Real Code Generation
- Generates actual, production-ready code
- Not templates or scaffolds
- Language-specific best practices
- Proper error handling and logging
- Type hints and documentation

### Real Execution
- Actual file creation in Docker workspaces
- Real package installation (pip, npm, etc.)
- Real build processes (webpack, vite, etc.)
- Real test execution (pytest, jest, etc.)
- Proper error capture and analysis

### Self-Healing Capabilities
```python
while errors_detected:
    error = capture_latest_error()
    analysis = healing_agent.analyze(error)
    fix = healing_agent.generate_fix(analysis)
    apply_patch(fix)
    rerun_tests()
```

### Parallel Execution
- Frontend, Backend, Database, API, and DevOps agents run in parallel
- Reduces total execution time significantly
- Maintains dependency order
- Safe concurrent state management

### Token Tracking
- Per-task token counting
- Total cost estimation
- Model-specific optimizations
- Budget constraints support

## API Endpoints

### Execution

```
POST /api/orchestration/execute
Start autonomous workflow execution
Request:
{
  "project_name": "MyApp",
  "user_prompt": "Build a todo app...",
  "enable_self_healing": true,
  "max_iterations": 3
}
Response:
{
  "execution_id": "uuid",
  "status": "initialized",
  "websocket_url": "/api/orchestration/ws/uuid"
}

GET /api/orchestration/status/{execution_id}
Get execution status

WebSocket /api/orchestration/ws/{execution_id}
Real-time streaming

POST /api/orchestration/cancel/{execution_id}
Cancel execution

GET /api/orchestration/artifacts/{execution_id}
List generated artifacts

GET /api/orchestration/artifacts/{execution_id}/{artifact_id}
Download specific artifact
```

## LLM Model Configuration

### Recommended Setup
- **Planning/Reasoning**: Gemini 2.5 Pro or Claude 3.5 Sonnet
- **Code Generation**: Qwen2.5-Coder or DeepSeek-Coder
- **Fast Tasks**: Groq Llama 3.1 8B

### Token Economics
- Planning phase: ~3000 tokens
- Architecture: ~2500 tokens
- Code generation: ~4000-6000 tokens per agent (5 agents in parallel)
- Testing: ~2000 tokens
- Self-healing: ~2000-4000 tokens

**Total per project**: ~30,000-40,000 tokens
**Cost estimate**: $0.10-$0.30 per full project

## Frontend Components

### Builder Page (`/builder`)
- Main interface for project generation
- Shows execution timeline in real-time
- Displays generated artifacts
- Shows agent status dashboard
- Live log streaming

### Workspace Sidebar
- File tree view of generated artifacts
- Click to preview code
- Organized by directory structure
- Shows file count and size

### Live Preview Panel
- Code syntax highlighting
- HTML preview capability
- Language-specific rendering
- Export functionality

### Execution Timeline
- Visual timeline of agent execution
- Current task indicator
- Error indicators
- Phase completion tracking

### Agent Status Dashboard
- Real-time status of all 11 agents
- Animated loading indicators
- Error highlighting
- Success checkmarks

## Database Schema

Key tables for production:

```sql
-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  user_prompt TEXT NOT NULL,
  refined_prompt TEXT,
  status VARCHAR,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Runs
CREATE TABLE runs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  status VARCHAR,
  total_tokens INT,
  cost DECIMAL,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- Artifacts
CREATE TABLE artifacts (
  id UUID PRIMARY KEY,
  run_id UUID REFERENCES runs(id),
  path VARCHAR NOT NULL,
  content TEXT NOT NULL,
  language VARCHAR,
  generated_by VARCHAR,
  created_at TIMESTAMP
);

-- Executions
CREATE TABLE executions (
  id UUID PRIMARY KEY,
  run_id UUID REFERENCES runs(id),
  agent_role VARCHAR,
  status VARCHAR,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  tokens_used INT,
  error_message TEXT
);
```

## Deployment

### Docker Compose
```bash
docker-compose up -d
```

### Environment Variables
```env
# LLM Configuration
LLM_PROVIDER=openai  # or gemini, anthropic, etc.
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@localhost/agentflow

# Redis
REDIS_URL=redis://localhost:6379

# Observability
OMIUM_API_KEY=...
SENTRY_DSN=...
```

### Scaling
- Use Kubernetes for multi-workspace management
- Scale agents as separate microservices
- Use Redis Celery for distributed task queue
- PostgreSQL for persistent storage
- S3/GCS for artifact storage

## Performance Characteristics

- **Time to generate complete project**: 2-5 minutes
- **Real-time WebSocket latency**: <100ms
- **Workspace creation**: <500ms
- **Artifact generation per agent**: 30-90 seconds
- **Self-healing iteration**: 1-2 minutes

## Monitoring & Observability

- **Omnium SDK** for distributed tracing
- **Structured logging** for all agent operations
- **Prometheus metrics** for performance monitoring
- **Error tracking** with automatic issue reporting
- **Cost tracking** per execution

## Security Considerations

1. **Sandboxing**: All code execution in isolated Docker containers
2. **API Key Management**: Secure credential storage
3. **Rate Limiting**: Per-user and per-project limits
4. **Audit Logging**: All actions logged with timestamps
5. **Output Sanitization**: Generated code validated before execution

## Future Enhancements

- [ ] Multi-language support (Go, Rust, Java, etc.)
- [ ] Interactive code refinement UI
- [ ] Project forking and versioning
- [ ] Collaborative real-time editing
- [ ] Advanced debugging tools
- [ ] Performance profiling
- [ ] Automated deployment to cloud platforms
- [ ] Mobile app code generation

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## License

MIT License - See LICENSE file
