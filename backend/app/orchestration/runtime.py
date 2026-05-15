from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.config import settings
from app.llm.client import Qwen3CoderClient
from app.orchestration.contracts import GeneratedArtifactContract, GeneratedPlanContract, PlanStepContract, RunOutcomeContract
from app.runtime.sandbox import ProjectSandbox, SandboxFile
from app.streams import stream_manager
from app.observability.event_store import execution_events

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentExecutionRecord:
    step_id: str
    agent: str
    status: str
    summary: str
    files: list[SandboxFile] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class AutonomousRunRuntime:
    def __init__(self, llm_client: Qwen3CoderClient | None = None) -> None:
        self.llm_client = llm_client or Qwen3CoderClient()
        self.max_self_heal_retries = settings.self_heal_max_retries

    def _step_role(self, agent_name: str) -> str:
        normalized = agent_name.lower()
        if "prompt" in normalized and "refine" in normalized:
            return "prompt_refinement"
        if "planner" in normalized:
            return "planner"
        if "architect" in normalized or "architecture" in normalized:
            return "architect"
        if "frontend" in normalized:
            return "frontend"
        if "backend" in normalized:
            return "backend"
        if "database" in normalized:
            return "database"
        if "integrat" in normalized:
            return "integration"
        if "test" in normalized:
            return "testing"
        if "heal" in normalized:
            return "self_healing"
        if "debug" in normalized:
            return "self_healing"
        return normalized.replace(" ", "_")

    async def _emit(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        execution_events.append(run_id, event_type, payload)
        await stream_manager.emit_event(run_id, event_type, payload)

    def _artifact_from_file(self, file: SandboxFile, agent: str, step_id: str) -> GeneratedArtifactContract:
        return GeneratedArtifactContract(
            kind=agent,
            path=file.path,
            content=file.content,
            artifact_metadata={"step": step_id, "agent": agent, "explanation": file.explanation or ""},
        )

    def _default_pipeline(self, plan: GeneratedPlanContract) -> list[PlanStepContract]:
        return plan.steps or [
            PlanStepContract(id="refine", title="Refine prompt", agent="Prompt Refinement Agent", description="Clarify the product request."),
            PlanStepContract(id="planner", title="Plan execution", agent="Planner Agent", description="Break the request into an execution graph.", dependencies=["refine"]),
            PlanStepContract(id="architect", title="Design architecture", agent="Architecture Agent", description="Define the codebase structure, data model, and contracts.", dependencies=["planner"]),
            PlanStepContract(id="frontend", title="Generate frontend", agent="Frontend Agent", description="Generate the React/Next.js UI and streaming workspace.", dependencies=["architect"]),
            PlanStepContract(id="backend", title="Generate backend", agent="Backend Agent", description="Generate FastAPI routes, services, and orchestration hooks.", dependencies=["architect"]),
            PlanStepContract(id="database", title="Generate database", agent="Database Agent", description="Generate schema and migrations.", dependencies=["architect"]),
            PlanStepContract(id="integration", title="Integrate systems", agent="Integration Agent", description="Wire client, API, storage, and execution flows.", dependencies=["frontend", "backend", "database"]),
            PlanStepContract(id="testing", title="Run tests", agent="Testing Agent", description="Generate and run build, lint, and smoke tests.", dependencies=["integration"]),
            PlanStepContract(id="self_healing", title="Self-heal build failures", agent="Self-Healing Agent", description="Repair build and runtime errors until the workspace is healthy.", dependencies=["testing"]),
        ]

    async def execute_plan_async(self, plan: GeneratedPlanContract, run_id: str) -> RunOutcomeContract:
        sandbox = ProjectSandbox(plan.project_id)
        workspace = sandbox.ensure()
        artifacts: list[GeneratedArtifactContract] = []
        timeline: list[dict[str, Any]] = []
        context: dict[str, Any] = {
            "request": plan.objective,
            "project_name": plan.project_name,
            "workspace_path": str(workspace),
            "architecture": {},
            "requirements": "",
            "artifacts": [],
            "timeline": timeline,
        }

        await self._emit(run_id, "run_started", {"run_id": run_id, "workspace_path": str(workspace), "project_id": plan.project_id})

        steps = self._default_pipeline(plan)
        step_map = {step.id: step for step in steps}
        completed: set[str] = set()
        pending = {step.id: step for step in steps}

        async def run_step(step: PlanStepContract) -> AgentExecutionRecord:
            await self._emit(run_id, "agent_started", {"step_id": step.id, "agent": step.agent, "title": step.title})
            try:
                result = await self.llm_client.a_execute_agent_task(self._step_role(step.agent), step.description, context)
                files = [SandboxFile(path=item["path"], content=item["content"], explanation=item.get("explanation")) for item in result.get("files", []) if isinstance(item, dict) and item.get("path") and item.get("content")]
                if files:
                    sandbox.write_files(files)
                    artifacts.extend(self._artifact_from_file(file, step.agent, step.id) for file in files)
                context[step.id] = result
                if step.id in {"architect", "planner"}:
                    context["architecture"] = result.get("system_architecture", result.get("roadmap", result))
                    context["requirements"] = result.get("clarified_requirements", context.get("requirements", ""))
                timeline.append({"step_id": step.id, "agent": step.agent, "status": "completed", "summary": result.get("summary", step.description)})
                await self._emit(run_id, "agent_completed", {"step_id": step.id, "agent": step.agent, "artifact_count": len(files)})
                return AgentExecutionRecord(step_id=step.id, agent=step.agent, status="completed", summary=result.get("summary", step.description), files=files, token_usage=result.get("usage", {}), metadata=result)
            except Exception as exc:
                timeline.append({"step_id": step.id, "agent": step.agent, "status": "failed", "error": str(exc)})
                await self._emit(run_id, "agent_failed", {"step_id": step.id, "agent": step.agent, "error": str(exc)})
                raise

        # Execute dependency graph with simple ready-set scheduling.
        while pending:
            ready = [step for step in pending.values() if all(dep in completed for dep in step.dependencies)]
            if not ready:
                break
            results = await asyncio.gather(*(run_step(step) for step in ready))
            for record in results:
                completed.add(record.step_id)
                pending.pop(record.step_id, None)

        install_result = await sandbox.install_dependencies()
        if install_result is not None:
            timeline.append({"command": install_result.command, "returncode": install_result.returncode, "stdout": install_result.stdout[-2000:], "stderr": install_result.stderr[-2000:]})
            await self._emit(run_id, "sandbox_command", {"command": install_result.command, "returncode": install_result.returncode})

        build_result = await sandbox.build()
        lint_result = await sandbox.lint()

        repair_attempts = 0
        while repair_attempts < self.max_self_heal_retries and any(result is not None and result.returncode != 0 for result in (build_result, lint_result)):
            repair_attempts += 1
            failure_text = "\n\n".join(filter(None, [
                f"build stdout:\n{build_result.stdout if build_result else ''}\n{build_result.stderr if build_result else ''}",
                f"lint stdout:\n{lint_result.stdout if lint_result else ''}\n{lint_result.stderr if lint_result else ''}",
            ]))
            await self._emit(run_id, "self_heal_started", {"attempt": repair_attempts, "errors": failure_text[:4000]})
            repair_context = {
                **context,
                "error": failure_text,
                "build_result": asdict(build_result) if build_result else {},
                "lint_result": asdict(lint_result) if lint_result else {},
            }
            repair = await self.llm_client.a_execute_agent_task("self_healing", "Repair build failures", repair_context)
            repair_files = [SandboxFile(path=item["path"], content=item["content"], explanation=item.get("explanation")) for item in repair.get("files", []) if isinstance(item, dict) and item.get("path") and item.get("content")]
            if repair_files:
                sandbox.write_files(repair_files)
                artifacts.extend(self._artifact_from_file(file, "self_healing", "self_healing") for file in repair_files)
            build_result = await sandbox.build()
            lint_result = await sandbox.lint()
            await self._emit(run_id, "self_heal_completed", {"attempt": repair_attempts, "build_returncode": build_result.returncode if build_result else 0, "lint_returncode": lint_result.returncode if lint_result else 0})

        summary = f"Generated {len(artifacts)} artifacts across {len(completed)} autonomous steps."
        summary_content = "\n".join([
            "# Execution Summary",
            f"Project: {plan.project_name}",
            f"Objective: {plan.objective}",
            f"Workspace: {workspace}",
            f"Artifacts: {len(artifacts)}",
            f"Steps completed: {len(completed)}",
            "",
            "## Timeline",
            *[f"- {entry}" for entry in timeline],
        ])
        artifacts.append(GeneratedArtifactContract(kind="summary", path="docs/EXECUTION_SUMMARY.md", content=summary_content, artifact_metadata={"stage": "summary"}))

        await self._emit(run_id, "run_completed", {"run_id": run_id, "artifact_count": len(artifacts), "summary": summary})
        return RunOutcomeContract(run_id=run_id, status="completed", summary=summary, artifacts=artifacts)

    async def execute_plan_and_persist(self, plan: GeneratedPlanContract, run_id: str, db: Any = None) -> RunOutcomeContract:
        """Execute plan and persist outcomes to database.
        
        This is the async version that should be called from Celery tasks.
        """
        try:
            return await self.execute_plan_async(plan, run_id)
        except Exception as e:
            logger.error(f"Error executing plan {run_id}: {e}")
            await self._emit(run_id, "run_failed", {"error": str(e), "run_id": run_id})
            raise