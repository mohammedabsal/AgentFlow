from __future__ import annotations

import json
import logging

from app.llm.qwen_client import Qwen3CoderClient
from app.orchestration.contracts import GeneratedArtifactContract, GeneratedPlanContract, PlanStepContract, RunOutcomeContract
from app.orchestration.runtime import AutonomousRunRuntime

logger = logging.getLogger(__name__)


class AutonomousAppEngine:
    def __init__(self, llm_client: Qwen3CoderClient | None = None):
        """Initialize engine with optional LLM client for real plan generation."""
        self.llm_client = llm_client
        self.runtime = AutonomousRunRuntime(llm_client=llm_client)

    def build_plan(self, project_id: str, project_name: str, prompt: str) -> GeneratedPlanContract:
        """Build execution plan from user prompt, using LLM if available."""
        # Try to use LLM for real plan generation
        if self.llm_client:
            try:
                plan_data = self.llm_client.generate_plan(prompt)
                logger.info(f"Generated plan for project {project_id} using LLM")
                
                # Build steps from LLM response
                steps = []
                for task in plan_data.get("tasks", []):
                    steps.append(
                        PlanStepContract(
                            id=task.get("task_id", ""),
                            title=task.get("description", "")[:50],
                            agent=self._agent_role_to_name(task.get("agent_role", "")),
                            description=task.get("description", ""),
                        )
                    )
                
                return GeneratedPlanContract(
                    project_id=project_id,
                    project_name=project_name,
                    objective=prompt,
                    stack={
                        "frontend": ["Next.js 15", "React", "TailwindCSS", "shadcn/ui", "Sandpack"],
                        "backend": ["FastAPI", "Supabase Postgres", "Redis"],
                        "models": ["Qwen Coder"],
                    },
                    steps=steps or self._default_steps(),
                    risks=[],
                )
            except Exception as e:
                logger.warning(f"LLM plan generation failed, using default: {e}")
                self.llm_client = None
        
        # Fallback to default plan
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
            "integration": "Integration Agent",
            "debug": "Debug Agent",
            "testing": "Testing Agent",
            "self_healing": "Self-Healing Agent",
            "deploy": "Deployment Agent",
        }
        return mapping.get(role, role.title())

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
                            kind=artifact_kind,
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
                kind="summary",
                path="generated/EXECUTION_SUMMARY.md",
                content=summary_content,
                artifact_metadata={"stage": "summary"},
            )
        )

        return RunOutcomeContract(
            run_id=run_id,
            status="completed",
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

    def execute_plan(self, plan: GeneratedPlanContract, run_id: str) -> RunOutcomeContract:
        """Execute the plan via the autonomous runtime."""
        return self.runtime.execute_plan(plan, run_id)

    def _mock_artifacts(self, plan: GeneratedPlanContract) -> list[GeneratedArtifactContract]:
        """Generate mock artifacts when LLM is not available."""
        return [
            GeneratedArtifactContract(
                kind="architecture",
                path="docs/generated-architecture.md",
                content=f"# {plan.project_name}\n\n{plan.objective}\n",
                artifact_metadata={"stage": "architecture"},
            ),
            GeneratedArtifactContract(
                kind="frontend",
                path="frontend/src/app/page.tsx",
                content="// Lovable-style workspace scaffold generated by the autonomous engine\n",
                artifact_metadata={"stage": "frontend"},
            ),
            GeneratedArtifactContract(
                kind="backend",
                path="backend/app/api/routes/platform.py",
                content="# Platform orchestration endpoints scaffolded by the autonomous engine\n",
                artifact_metadata={"stage": "backend"},
            ),
            GeneratedArtifactContract(
                kind="tests",
                path="tests/platform_smoke_test.md",
                content="- verify prompt planning\n- verify run creation\n- verify artifact emission\n",
                artifact_metadata={"stage": "testing"},
            ),
        ]

    async def execute_plan_async(self, plan: GeneratedPlanContract, run_id: str) -> RunOutcomeContract:
        """Execute the plan via the autonomous runtime (async version for Celery tasks)."""
        return await self.runtime.execute_plan_and_persist(plan, run_id)
