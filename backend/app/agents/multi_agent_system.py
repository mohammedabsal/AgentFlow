"""
Multi-agent orchestration system for autonomous AI software engineering.

Implements 11 specialized agents:
1. Prompt Refiner - Clarifies user intent
2. Research Agent - Analyzes requirements and tech landscape
3. Planner - Breaks work into executable tasks
4. Architecture Agent - Designs system structure
5. Frontend Agent - Generates UI/UX code
6. Backend Agent - Generates server logic
7. Database Agent - Designs schema and queries
8. API Agent - Designs REST/GraphQL APIs
9. DevOps Agent - Creates deployment configs
10. Testing Agent - Generates tests and QA scripts
11. Self-Healing Agent - Analyzes and fixes errors
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.config import settings
from app.llm.client import LLMClient
from app.orchestration.contracts import (
    AgentRole,
    ArtifactType,
    ExecutionStatus,
    GeneratedArtifactContract,
    TaskContract,
    TaskExecutionState,
)

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Capability of an agent."""

    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    RESEARCH = "research"
    DESIGN = "design"
    TESTING = "testing"
    ERROR_FIXING = "error_fixing"


@dataclass
class AgentContext:
    """Shared context for all agents in a run."""

    execution_id: str
    project_id: str
    project_name: str
    user_prompt: str
    refined_prompt: str = ""
    research_findings: str = ""
    architecture_plan: str = ""
    tech_stack: dict[str, list[str]] = field(default_factory=dict)
    generated_artifacts: dict[str, GeneratedArtifactContract] = field(default_factory=dict)
    execution_errors: list[str] = field(default_factory=list)
    shared_memory: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTaskInput:
    """Input to an agent task."""

    task_id: str
    agent: AgentRole
    context: AgentContext
    requirements: str
    previous_outputs: list[GeneratedArtifactContract] = field(default_factory=list)
    budget_tokens: int = 8000


@dataclass
class AgentTaskOutput:
    """Output from an agent task."""

    task_id: str
    agent: AgentRole
    status: ExecutionStatus
    artifacts: list[GeneratedArtifactContract] = field(default_factory=list)
    tokens_used: int = 0
    logs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    execution_state: Optional[TaskExecutionState] = None


class BaseAgent(ABC):
    """Base agent class for all specialized agents."""

    def __init__(self, llm_client: LLMClient, role: AgentRole):
        """Initialize agent with LLM client."""
        self.llm_client = llm_client
        self.role = role
        self.name = role.value.replace("_", " ").title()

    @abstractmethod
    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Execute the agent task."""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[AgentCapability]:
        """Return capabilities of this agent."""
        pass

    async def call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Call LLM with prompt."""
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system=system_prompt or self._get_system_prompt(),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed for {self.name}: {e}")
            raise

    def _get_system_prompt(self) -> str:
        """Get system prompt for this agent."""
        base_prompt = (
            "You are an expert AI software engineer. "
            "Provide clear, production-ready solutions. "
            "Format code properly with good documentation."
        )
        return base_prompt


class PromptRefinerAgent(BaseAgent):
    """Refines and clarifies user intent into structured requirements."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.PROMPT_REFINER)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Refine user prompt into structured requirements."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Analyze and refine this user prompt into clear product requirements:

User Prompt: {task_input.context.user_prompt}

Provide:
1. Clarified objective
2. Key features required
3. Success criteria
4. Non-functional requirements (performance, scale, security)
5. Suggested tech stack

Be concise and specific.
"""

            refined = await self.call_llm(
                prompt=prompt,
                temperature=0.5,
                max_tokens=2000,
                system_prompt=self._get_system_prompt()
                + " Focus on clarity and specificity.",
            )

            task_input.context.refined_prompt = refined
            output.status = ExecutionStatus.COMPLETED
            output.logs = [f"Refined prompt: {refined[:200]}..."]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]
            logger.error(f"Prompt refinement failed: {e}")

        return output

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.ANALYSIS]


class ResearchAgent(BaseAgent):
    """Researches tech landscape and existing solutions."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.RESEARCH)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Research and analyze requirements."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Research the best approach for this project:

Refined Requirements: {task_input.context.refined_prompt}

Provide:
1. Relevant tech options and comparisons
2. Best practices for this type of application
3. Potential challenges and solutions
4. Industry standards and patterns
5. Recommended architecture style

Focus on production-ready recommendations.
"""

            research = await self.call_llm(
                prompt=prompt,
                temperature=0.6,
                max_tokens=2500,
            )

            task_input.context.research_findings = research
            output.status = ExecutionStatus.COMPLETED
            output.logs = [f"Research completed: {research[:200]}..."]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.RESEARCH, AgentCapability.ANALYSIS]


class PlannerAgent(BaseAgent):
    """Plans execution with task decomposition and dependencies."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.PLANNER)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Create execution plan with task decomposition."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Create a detailed execution plan with tasks and dependencies:

Refined Requirements: {task_input.context.refined_prompt}
Research: {task_input.context.research_findings}

Output a JSON object with:
{{
    "phases": [
        {{
            "name": "phase_name",
            "description": "what this phase does",
            "tasks": [
                {{
                    "id": "task_id",
                    "title": "task title",
                    "description": "what to do",
                    "agent": "agent_role",
                    "dependencies": ["task_ids"],
                    "estimated_tokens": 2000
                }}
            ]
        }}
    ],
    "critical_path": ["task_ids"],
    "parallelizable_groups": [["task_ids"]]
}}

Make tasks granular and parallelizable where possible.
"""

            plan_json = await self.call_llm(
                prompt=prompt,
                temperature=0.5,
                max_tokens=3000,
            )

            # Extract JSON from response
            try:
                import re

                json_match = re.search(r"\{.*\}", plan_json, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                    task_input.context.shared_memory["execution_plan"] = plan_data
            except (json.JSONDecodeError, AttributeError):
                pass

            output.status = ExecutionStatus.COMPLETED
            output.logs = ["Execution plan created successfully"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.PLANNING, AgentCapability.ANALYSIS]


class ArchitectureAgent(BaseAgent):
    """Designs system architecture and structure."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.ARCHITECT)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Design system architecture."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Design the complete system architecture:

Requirements: {task_input.context.refined_prompt}
Plan: {json.dumps(task_input.context.shared_memory.get('execution_plan', {}), indent=2)}

Provide:
1. System diagram description (components and flows)
2. Folder structure for frontend, backend, database
3. API endpoints and data models
4. Database schema (tables, relationships)
5. Key design patterns and principles
6. Scalability considerations

Output as structured markdown.
"""

            architecture = await self.call_llm(
                prompt=prompt,
                temperature=0.5,
                max_tokens=3000,
            )

            task_input.context.architecture_plan = architecture

            # Create architecture artifact
            artifact = GeneratedArtifactContract(
                artifact_id=f"{task_input.task_id}-architecture",
                kind=ArtifactType.SCHEMA,
                path="ARCHITECTURE.md",
                content=architecture,
                language="markdown",
                generated_by=self.role,
                artifact_metadata={"type": "design_document"},
            )

            output.artifacts = [artifact]
            output.status = ExecutionStatus.COMPLETED
            output.logs = ["Architecture designed successfully"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.DESIGN, AgentCapability.ANALYSIS]


class FrontendAgent(BaseAgent):
    """Generates frontend code (Next.js, React, Tailwind)."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.FRONTEND)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Generate frontend code."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Generate Next.js 15 + React + Tailwind + TypeScript frontend code:

Requirements: {task_input.context.refined_prompt}
Architecture: {task_input.context.architecture_plan[:2000]}

Generate:
1. page.tsx - main page component
2. layout.tsx - root layout with Tailwind
3. components/Header.tsx - navigation header
4. components/Hero.tsx - hero section
5. styles/globals.css - global styles
6. package.json - dependencies
7. tailwind.config.ts - Tailwind config
8. tsconfig.json - TypeScript config

Use shadcn/ui components where applicable. Make it production-ready and beautiful.
Return each file as:
FILE: path/to/file
LANGUAGE: language
CODE:
```
...code...
```
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000,
                system_prompt=self._get_system_prompt() + " Expert frontend architect.",
            )

            # Parse generated files
            artifacts = self._parse_generated_files(code, "typescript")
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = [f"Generated {len(artifacts)} frontend files"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str, language: str) -> list[GeneratedArtifactContract]:
        """Parse generated files from LLM response."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"frontend-{current_file.replace('/', '-')}",
                        kind=ArtifactType.FILE,
                        path=current_file,
                        content="\n".join(current_content),
                        language=language,
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.CODE_GENERATION, AgentCapability.DESIGN]


class BackendAgent(BaseAgent):
    """Generates backend code (FastAPI, Python)."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.BACKEND)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Generate backend code."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Generate FastAPI Python backend code:

Requirements: {task_input.context.refined_prompt}
Architecture: {task_input.context.architecture_plan[:2000]}

Generate:
1. main.py - FastAPI app initialization
2. config.py - environment configuration
3. models.py - Pydantic schemas
4. routers/api.py - API endpoints
5. routers/health.py - health check
6. database.py - database setup (if needed)
7. requirements.txt - dependencies
8. Dockerfile - Docker configuration
9. .env.example - environment template

Make production-ready with proper error handling and logging.
Return each file as:
FILE: path/to/file
LANGUAGE: language
CODE:
```
...code...
```
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000,
                system_prompt=self._get_system_prompt() + " Expert backend architect.",
            )

            artifacts = self._parse_generated_files(code, "python")
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = [f"Generated {len(artifacts)} backend files"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str, language: str) -> list[GeneratedArtifactContract]:
        """Parse generated files from LLM response."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"backend-{current_file.replace('/', '-')}",
                        kind=ArtifactType.FILE,
                        path=current_file,
                        content="\n".join(current_content),
                        language=language,
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.CODE_GENERATION, AgentCapability.DESIGN]


class DatabaseAgent(BaseAgent):
    """Designs database schema and queries."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.DATABASE)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Design database schema."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Design PostgreSQL database schema:

Requirements: {task_input.context.refined_prompt}
Architecture: {task_input.context.architecture_plan[:2000]}

Generate:
1. schema.sql - complete database schema with tables, indexes, constraints
2. migrations/ - migration files if needed
3. queries.py - common database queries (if using Python)
4. README.md - schema documentation

Include:
- Proper relationships and foreign keys
- Indexes for performance
- Constraints for data integrity
- Comments explaining each table
- Example queries for common operations

Return each file as:
FILE: path/to/file
CODE:
```
...code...
```
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.6,
                max_tokens=3000,
                system_prompt=self._get_system_prompt() + " Expert database architect.",
            )

            artifacts = self._parse_generated_files(code)
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = ["Database schema designed successfully"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str) -> list[GeneratedArtifactContract]:
        """Parse generated files from LLM response."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"db-{current_file.replace('/', '-')}",
                        kind=ArtifactType.FILE,
                        path=current_file,
                        content="\n".join(current_content),
                        language="sql" if current_file.endswith(".sql") else "python",
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.DESIGN, AgentCapability.ANALYSIS]


class APIAgent(BaseAgent):
    """Designs REST/GraphQL APIs."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.API)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Design API specification."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Design REST API specification (OpenAPI/Swagger):

Requirements: {task_input.context.refined_prompt}

Generate:
1. API design document with endpoints
2. Request/response schemas
3. Authentication method
4. Error handling strategy
5. Rate limiting policy
6. Versioning strategy
7. openapi.yaml - OpenAPI specification

Include at least 10 endpoints covering CRUD operations and key features.
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.6,
                max_tokens=3000,
            )

            artifacts = self._parse_generated_files(code)
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = ["API specification designed"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str) -> list[GeneratedArtifactContract]:
        """Parse generated files."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"api-{current_file.replace('/', '-')}",
                        kind=ArtifactType.FILE,
                        path=current_file,
                        content="\n".join(current_content),
                        language="yaml" if current_file.endswith(".yaml") else "markdown",
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.DESIGN, AgentCapability.ANALYSIS]


class DevOpsAgent(BaseAgent):
    """Creates deployment and infrastructure configs."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.DEVOPS)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Generate DevOps configs."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Generate deployment and infrastructure configs:

Requirements: {task_input.context.refined_prompt}

Generate:
1. docker-compose.yml - local development
2. Dockerfile.prod - production image
3. .github/workflows/ci.yml - GitHub Actions CI/CD
4. kubernetes/deployment.yaml - K8s deployment (if applicable)
5. nginx.conf - reverse proxy config
6. .env.production - production environment template
7. DEPLOYMENT.md - deployment guide
8. healthcheck scripts

Make production-ready and scalable.
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.6,
                max_tokens=3000,
            )

            artifacts = self._parse_generated_files(code)
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = ["DevOps configs generated"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str) -> list[GeneratedArtifactContract]:
        """Parse generated files."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"devops-{current_file.replace('/', '-')}",
                        kind=ArtifactType.FILE,
                        path=current_file,
                        content="\n".join(current_content),
                        language="yaml",
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.CODE_GENERATION, AgentCapability.DESIGN]


class TestingAgent(BaseAgent):
    """Generates comprehensive tests."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.TESTING)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Generate test suite."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            prompt = f"""
Generate comprehensive test suite:

Requirements: {task_input.context.refined_prompt}

Generate:
1. tests/test_api.py - API endpoint tests (pytest)
2. tests/test_models.py - model/schema tests
3. tests/test_integration.py - integration tests
4. tests/conftest.py - pytest fixtures
5. tests/e2e.py - end-to-end tests
6. jest.config.js - frontend testing config (if applicable)
7. __tests__/components.test.tsx - React component tests
8. coverage report configuration

Include:
- Unit tests with >80% coverage target
- Integration tests
- Mocking where appropriate
- Test data factories
- CI/CD ready test runner config
"""

            code = await self.call_llm(
                prompt=prompt,
                temperature=0.6,
                max_tokens=3000,
            )

            artifacts = self._parse_generated_files(code)
            output.artifacts = artifacts
            output.status = ExecutionStatus.COMPLETED
            output.logs = ["Test suite generated"]

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def _parse_generated_files(self, content: str) -> list[GeneratedArtifactContract]:
        """Parse generated files."""
        artifacts = []
        current_file = None
        current_content = []
        in_code = False

        for line in content.split("\n"):
            if line.startswith("FILE:"):
                if current_file:
                    artifact = GeneratedArtifactContract(
                        artifact_id=f"test-{current_file.replace('/', '-')}",
                        kind=ArtifactType.TEST,
                        path=current_file,
                        content="\n".join(current_content),
                        language="python" if current_file.endswith(".py") else "typescript",
                        generated_by=self.role,
                    )
                    artifacts.append(artifact)
                current_file = line.replace("FILE:", "").strip()
                current_content = []
            elif line.startswith("```"):
                in_code = not in_code
            elif in_code and current_file:
                current_content.append(line)

        return artifacts

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.CODE_GENERATION, AgentCapability.TESTING]


class SelfHealingAgent(BaseAgent):
    """Analyzes errors and generates fixes."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, AgentRole.SELF_HEALING)

    async def execute(self, task_input: AgentTaskInput) -> AgentTaskOutput:
        """Analyze errors and generate fixes."""
        output = AgentTaskOutput(
            task_id=task_input.task_id,
            agent=self.role,
            status=ExecutionStatus.PENDING,
        )

        try:
            errors = "\n".join(task_input.context.execution_errors[-5:])  # Last 5 errors
            prompt = f"""
Analyze these errors and provide fixes:

Errors:
{errors}

Generated files:
{json.dumps({k: v.path for k, v in task_input.context.generated_artifacts.items()}, indent=2)}

For each error:
1. Explain the root cause
2. Identify which file needs fixing
3. Provide the corrected code
4. Explain why it fixes the issue

Format as:
ERROR: [error message]
FILE: [file path]
FIX:
```
...corrected code...
```
EXPLANATION: [why this fixes it]
"""

            fixes = await self.call_llm(
                prompt=prompt,
                temperature=0.5,
                max_tokens=3000,
            )

            output.status = ExecutionStatus.COMPLETED
            output.logs = ["Fixes generated successfully"]
            task_input.context.shared_memory["fixes"] = fixes

        except Exception as e:
            output.status = ExecutionStatus.FAILED
            output.errors = [str(e)]

        return output

    def get_capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.ERROR_FIXING, AgentCapability.ANALYSIS]


# Agent factory for getting agent instances
AGENT_REGISTRY: dict[AgentRole, type[BaseAgent]] = {
    AgentRole.PROMPT_REFINER: PromptRefinerAgent,
    AgentRole.RESEARCH: ResearchAgent,
    AgentRole.PLANNER: PlannerAgent,
    AgentRole.ARCHITECT: ArchitectureAgent,
    AgentRole.FRONTEND: FrontendAgent,
    AgentRole.BACKEND: BackendAgent,
    AgentRole.DATABASE: DatabaseAgent,
    AgentRole.API: APIAgent,
    AgentRole.DEVOPS: DevOpsAgent,
    AgentRole.TESTING: TestingAgent,
    AgentRole.SELF_HEALING: SelfHealingAgent,
}


def get_agent(role: AgentRole, llm_client: LLMClient) -> BaseAgent:
    """Factory function to get agent instance."""
    agent_class = AGENT_REGISTRY.get(role)
    if not agent_class:
        raise ValueError(f"Unknown agent role: {role}")

    # Route to a specific provider or model if configured for this agent
    provider_override = getattr(settings, "agent_providers", {}).get(role.value)
    model_override = getattr(settings, "agent_models", {}).get(role.value)
    
    if provider_override or model_override:
        original_provider = settings.llm_provider
        original_model = settings.llm_model
        if provider_override:
            settings.llm_provider = provider_override
        if model_override:
            settings.llm_model = model_override
        try:
            agent_llm = LLMClient()
        finally:
            settings.llm_provider = original_provider
            settings.llm_model = original_model
        return agent_class(agent_llm)

    return agent_class(llm_client)
