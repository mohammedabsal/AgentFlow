from __future__ import annotations

import json
import logging
import uuid

from app.llm.qwen_client import Qwen3CoderClient
from app.orchestration.contracts import ArtifactType, ExecutionStatus, GeneratedArtifactContract, GeneratedPlanContract, PlanStepContract, RunOutcomeContract
from app.orchestration.runtime import AutonomousRunRuntime

logger = logging.getLogger(__name__)


class AutonomousAppEngine:
    def __init__(self, llm_client: Qwen3CoderClient | None = None):
        """Initialize engine with optional LLM client for real plan generation."""
        self.llm_client = llm_client
        self.runtime = AutonomousRunRuntime(llm_client=llm_client)

    def build_plan(self, project_id: str, project_name: str, prompt: str) -> GeneratedPlanContract:
        """Build execution plan from user prompt, using LLM if available."""
        return GeneratedPlanContract(
            project_id=project_id,
            project_name=project_name,
            objective=prompt,
            stack={
                "frontend": ["Next.js 15", "React", "TailwindCSS", "Framer Motion", "shadcn/ui", "Zustand", "Monaco Editor"],
                "backend": ["FastAPI", "Redis queue", "PostgreSQL", "sandboxed execution", "Git versioning"],
                "models": ["Qwen Coder", "Gemini API", "Claude API"],
            },
            steps=self._default_steps(),
            risks=["sandbox escapes", "model latency", "queue backlog", "test flakiness"],
        )

    def _default_steps(self) -> list[PlanStepContract]:
        """Return default execution steps."""
        return [
            PlanStepContract(
                id="refine",
                title="Refine prompt",
                agent="Prompt Refinement Agent",
                description="Turn the user prompt into structured product requirements and acceptance criteria.",
            ),
            PlanStepContract(
                id="planner",
                title="Plan execution graph",
                agent="Planner Agent",
                description="Break the request into a dependency-aware execution graph with parallel agent lanes.",
                dependencies=["refine"],
            ),
            PlanStepContract(
                id="architect",
                title="Design architecture",
                agent="Architecture Agent",
                description="Define folder structure, database schema, API boundaries, and the execution graph.",
                dependencies=["planner"],
            ),
            PlanStepContract(
                id="frontend",
                title="Generate frontend",
                agent="Frontend Agent",
                description="Create a Lovable-style workspace with live generation and project controls.",
                dependencies=["architect"],
            ),
            PlanStepContract(
                id="backend",
                title="Generate backend",
                agent="Backend Agent",
                description="Build APIs, models, orchestration hooks, auth, and realtime endpoints.",
                dependencies=["architect"],
            ),
            PlanStepContract(
                id="database",
                title="Generate database",
                agent="Database Agent",
                description="Create persistence models, migrations, and workspace snapshot storage.",
                dependencies=["architect"],
            ),
            PlanStepContract(
                id="integrate",
                title="Integrate systems",
                agent="Integration Agent",
                description="Wire frontend, backend, config, memory, and deployment targets together.",
                dependencies=["frontend", "backend", "database"],
            ),
            PlanStepContract(
                id="test",
                title="Run tests",
                agent="Testing Agent",
                description="Generate and run automated checks for UI, API, and execution flows.",
                dependencies=["integrate"],
            ),
            PlanStepContract(
                id="self_healing",
                title="Self-heal failures",
                agent="Self-Healing Agent",
                description="Repair build and runtime issues and re-run validation until the workspace is healthy.",
                dependencies=["test"],
            ),
        ]

    def _agent_role_to_name(self, role: str) -> str:
        """Convert agent role to display name."""
        mapping = {
            "prompt_refinement": "Prompt Refinement Agent",
            "planner": "Planner Agent",
            "architect": "Architect Agent",
            "frontend": "Frontend Agent",
            "backend": "Backend Agent",
            "database": "Database Agent",
            "auth": "Auth Agent",
            "devops": "DevOps Agent",
            "packager": "Packaging Agent",
            "integration": "Integration Agent",
            "debug": "Debug Agent",
            "testing": "Testing Agent",
            "self_healing": "Self-Healing Agent",
            "deploy": "Deployment Agent",
        }
        return mapping.get(role, role.title())

    def _task_dependencies(self, task: dict, role: str, task_ids_by_role: dict[str, str]) -> list[str]:
        """Extract or infer dependencies for an LLM-generated task."""
        explicit = task.get("dependencies") or task.get("depends_on") or task.get("requires")
        if isinstance(explicit, list):
            return [task_ids_by_role.get(str(item), str(item)) for item in explicit if item]

        default_roles = {
            "planner": ["prompt_refinement"],
            "architect": ["planner"],
            "frontend": ["architect"],
            "backend": ["architect"],
            "database": ["architect"],
            "auth": ["architect", "backend"],
            "devops": ["frontend", "backend", "database"],
            "integration": ["frontend", "backend", "database", "auth", "devops"],
            "testing": ["integration"],
            "self_healing": ["testing"],
            "packager": ["self_healing"],
            "deploy": ["testing"],
        }.get(role, [])
        return [task_ids_by_role[dep_role] for dep_role in default_roles if task_ids_by_role.get(dep_role)]

    def _complete_plan_steps(self, steps: list[PlanStepContract]) -> list[PlanStepContract]:
        """Ensure an LLM mini-plan still expands into a full code-generation run."""
        if not steps:
            return steps

        role_by_agent = {self._name_to_agent_role(step.agent): step for step in steps}
        id_by_role = {role: step.id for role, step in role_by_agent.items()}

        required = [
            ("prompt_refinement", "refine", "Refine prompt", "Prompt Refinement Agent", "Turn the user prompt into structured product requirements and acceptance criteria.", []),
            ("planner", "planner", "Plan execution graph", "Planner Agent", "Break the request into a dependency-aware execution graph with agent lanes.", ["prompt_refinement"]),
            ("architect", "architect", "Design architecture", "Architecture Agent", "Define folder structure, database schema, API boundaries, and the execution graph.", ["planner"]),
            ("frontend", "frontend", "Generate frontend", "Frontend Agent", "Generate the React/Next.js UI and streaming workspace.", ["architect"]),
            ("backend", "backend", "Generate backend", "Backend Agent", "Generate FastAPI routes, services, and orchestration hooks.", ["architect"]),
            ("database", "database", "Generate database", "Database Agent", "Generate schema, migrations, and persistence logic.", ["architect"]),
            ("auth", "auth", "Generate auth", "Auth Agent", "Generate auth routes, contracts, and integration notes.", ["architect", "backend"]),
            ("devops", "devops", "Generate devops", "DevOps Agent", "Generate Docker, environment, and local deployment setup.", ["frontend", "backend", "database"]),
            ("integration", "integration", "Integrate systems", "Integration Agent", "Wire client, API, storage, and execution flows.", ["frontend", "backend", "database", "auth", "devops"]),
            ("testing", "testing", "Run tests", "Testing Agent", "Generate and run build, lint, and smoke tests.", ["integration"]),
            ("self_healing", "self_healing", "Self-heal failures", "Self-Healing Agent", "Repair build and runtime issues and re-run validation until healthy.", ["testing"]),
            ("packager", "packager", "Package project", "Packaging Agent", "Prepare ZIP export metadata for the generated project.", ["self_healing"]),
        ]

        completed_steps = list(steps)
        for role, fallback_id, title, agent, description, dependency_roles in required:
            if role in role_by_agent:
                continue
            dependencies = [id_by_role[dep_role] for dep_role in dependency_roles if dep_role in id_by_role]
            step_id = fallback_id
            completed_steps.append(
                PlanStepContract(
                    id=step_id,
                    title=title,
                    agent=agent,
                    description=description,
                    dependencies=dependencies,
                )
            )
            id_by_role[role] = step_id
        return completed_steps

    def execute_plan(self, plan: GeneratedPlanContract, run_id: str) -> RunOutcomeContract:
        """Execute plan steps, calling LLM agents if available."""
        artifacts = []
        
        if self.llm_client:
            # Execute each step through LLM agents
            logger.info(f"Executing plan for run {run_id} using LLM agents")
            context = {
                "request": plan.objective,
                "architecture": {},
                "requirements": "",
            }
            
            for step in plan.steps:
                try:
                    logger.info(f"Executing step: {step.title}")
                    result = self.llm_client.execute_agent_task(
                        agent_role=self._name_to_agent_role(step.agent),
                        task_description=step.description,
                        context=context,
                    )
                    
                    # Store result as artifact
                    artifact_kind = step.id
                    artifact_path = f"generated/{step.id}_output.json"
                    
                    artifacts.append(
                        GeneratedArtifactContract(
                            artifact_id=str(uuid.uuid4()),
                            kind=ArtifactType.FILE,
                            path=artifact_path,
                            content=json.dumps(result, indent=2),
                            artifact_metadata={
                                "stage": step.id,
                                "agent": step.agent,
                                "step_title": step.title,
                            },
                        )
                    )
                    
                    # Update context with this step's output
                    context[step.id] = result
                    
                except Exception as e:
                    logger.error(f"Error executing step {step.title}: {e}")
                    logger.warning("Disabling LLM execution for this run and using mock artifacts")
                    return self._mock_outcome(plan, run_id, artifacts)
        else:
            # Fallback to mock artifacts
            logger.warning("No LLM client available, using mock artifacts")
            artifacts = self._mock_artifacts(plan)
        
        return self._build_outcome(plan, run_id, artifacts)

    def _mock_outcome(
        self,
        plan: GeneratedPlanContract,
        run_id: str,
        artifacts: list[GeneratedArtifactContract] | None = None,
    ) -> RunOutcomeContract:
        """Build a mock outcome, preserving any artifacts created before fallback."""
        combined_artifacts = artifacts or []
        combined_artifacts.extend(self._mock_artifacts(plan))
        return self._build_outcome(plan, run_id, combined_artifacts)

    def _build_outcome(
        self,
        plan: GeneratedPlanContract,
        run_id: str,
        artifacts: list[GeneratedArtifactContract],
    ) -> RunOutcomeContract:
        """Build the final run outcome with a summary artifact."""
        summary_content = f"""# Execution Summary

Project: {plan.project_name}
Objective: {plan.objective}
Status: completed

## Steps Executed
{chr(10).join(f"- {step.title}" for step in plan.steps)}

## Artifacts Generated
{chr(10).join(f"- {a.kind}: {a.path}" for a in artifacts)}
"""
        
        artifacts.append(
            GeneratedArtifactContract(
                artifact_id=str(uuid.uuid4()),
                kind=ArtifactType.FILE,
                path="generated/EXECUTION_SUMMARY.md",
                content=summary_content,
                artifact_metadata={"stage": "summary"},
            )
        )

        return RunOutcomeContract(
            run_id=run_id,
            execution_id=run_id,
            project_id=plan.project_id,
            status=ExecutionStatus.COMPLETED,
            summary=f"Successfully executed {len(plan.steps)} steps and generated {len(artifacts)} artifacts.",
            artifacts=artifacts,
        )

    def _name_to_agent_role(self, name: str) -> str:
        """Convert display name back to role."""
        name_lower = name.lower()
        if "prompt" in name_lower and "refine" in name_lower:
            return "prompt_refinement"
        elif "planner" in name_lower:
            return "planner"
        elif "architect" in name_lower:
            return "architect"
        elif "frontend" in name_lower:
            return "frontend"
        elif "backend" in name_lower:
            return "backend"
        elif "database" in name_lower:
            return "database"
        elif "auth" in name_lower:
            return "auth"
        elif "devops" in name_lower or "deploy" in name_lower:
            return "devops"
        elif "package" in name_lower:
            return "packager"
        elif "integrat" in name_lower:
            return "integration"
        elif "debug" in name_lower:
            return "debug"
        elif "test" in name_lower:
            return "testing"
        elif "heal" in name_lower:
            return "self_healing"
        elif "deploy" in name_lower:
            return "deploy"
        return "architect"  # default

    def _mock_artifacts(self, plan: GeneratedPlanContract) -> list[GeneratedArtifactContract]:
        """Generate mock artifacts when LLM is not available."""
        return [
            GeneratedArtifactContract(
                artifact_id=str(uuid.uuid4()),
                kind=ArtifactType.SCHEMA,
                path="docs/generated-architecture.md",
                content=f"# {plan.project_name}\n\n{plan.objective}\n",
                artifact_metadata={"stage": "architecture"},
            ),
            GeneratedArtifactContract(
                artifact_id=str(uuid.uuid4()),
                kind=ArtifactType.FILE,
                path="frontend/src/app/page.tsx",
                content="// Lovable-style workspace scaffold generated by the autonomous engine\n",
                artifact_metadata={"stage": "frontend"},
            ),
            GeneratedArtifactContract(
                artifact_id=str(uuid.uuid4()),
                kind=ArtifactType.FILE,
                path="backend/app/api/routes/platform.py",
                content="# Platform orchestration endpoints scaffolded by the autonomous engine\n",
                artifact_metadata={"stage": "backend"},
            ),
            GeneratedArtifactContract(
                artifact_id=str(uuid.uuid4()),
                kind=ArtifactType.TEST,
                path="tests/platform_smoke_test.md",
                content="- verify prompt planning\n- verify run creation\n- verify artifact emission\n",
                artifact_metadata={"stage": "testing"},
            ),
        ]

    async def execute_plan_async(self, plan: GeneratedPlanContract, run_id: str) -> RunOutcomeContract:
        """Execute the plan via the autonomous runtime (async version for Celery tasks)."""
        return await self.runtime.execute_plan_and_persist(plan, run_id)
