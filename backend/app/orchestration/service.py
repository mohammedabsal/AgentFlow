from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Artifact, Plan, Project, Run, Workspace
from app.llm.qwen_client import Qwen3CoderClient
from app.orchestration.contracts import GeneratedPlanContract, PlanStepContract, RunOutcomeContract
from app.orchestration.engine import AutonomousAppEngine
from app.queues.celery_app import celery_app

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProjectExecutionResult:
    project: Project
    plan: Plan
    run: Run
    outcome: RunOutcomeContract
    plan_snapshot: GeneratedPlanContract
    artifacts: list[Artifact]


class AutonomousProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        
        # Try to initialize LLM client; gracefully fall back to mock if not configured
        try:
            self.llm_client = Qwen3CoderClient()
            logger.info("Initialized Qwen Coder client for autonomous plan generation")
        except (ValueError, ImportError) as e:
            logger.warning(f"Could not initialize LLM client, using mock mode: {e}")
            self.llm_client = None
        
        self.engine = AutonomousAppEngine(llm_client=self.llm_client)

    def _get_or_create_workspace(self, workspace_id: str | None, workspace_name: str) -> Workspace:
        if workspace_id:
            workspace = self.db.get(Workspace, workspace_id)
            if workspace is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
            return workspace

        workspace = self.db.scalars(select(Workspace).order_by(Workspace.created_at.asc())).first()
        if workspace is not None:
            return workspace

        workspace = Workspace(name=workspace_name)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def create_project(self, *, workspace_id: str | None, workspace_name: str, name: str, prompt: str, description: str | None, project_metadata: dict[str, object]) -> Project:
        workspace = self._get_or_create_workspace(workspace_id, workspace_name)
        project = Project(
            workspace_id=workspace.id,
            name=name,
            prompt=prompt,
            description=description,
            status="active",
            project_metadata=project_metadata,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def build_plan(self, project: Project, objective: str | None = None) -> tuple[Plan, GeneratedPlanContract]:
        plan_snapshot = self.engine.build_plan(project.id, project.name, objective or project.prompt)
        plan = Plan(
            project_id=project.id,
            title=f"{project.name} launch plan",
            objective=plan_snapshot.objective,
            roadmap=[step.model_dump() for step in plan_snapshot.steps],
            stack=plan_snapshot.stack,
            status="ready",
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan, plan_snapshot

    def execute_project(self, project: Project, plan: Plan, plan_snapshot: GeneratedPlanContract) -> Run:
        """Create a run and dispatch execution to background task (returns immediately with queued run)."""
        run = Run(
            project_id=project.id,
            plan_id=plan.id,
            status="queued",
            prompt_input={"prompt": project.prompt},
            state={"phase": "queued", "step": 0},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        # Dispatch to background execution
        try:
            # Try Celery task first (production with Redis/workers)
            from app.queues.tasks import execute_project_task
            execute_project_task.delay(
                project_id=str(project.id),
                plan_id=str(plan.id),
                run_id=str(run.id),
                plan_snapshot_dict=plan_snapshot.model_dump(),
            )
            logger.info(f"Dispatched run {run.id} to Celery worker")
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}), using asyncio background task instead")
            # Fallback: use asyncio background task (development without Redis)
            asyncio.create_task(
                self._execute_project_async(
                    project_id=str(project.id),
                    plan_id=str(plan.id),
                    run_id=str(run.id),
                    plan_snapshot_dict=plan_snapshot.model_dump(),
                )
            )
        
        return run

    async def _execute_project_async(
        self,
        project_id: str,
        plan_id: str,
        run_id: str,
        plan_snapshot_dict: dict,
    ) -> None:
        """Background async execution of project plan (fallback for dev without Redis)."""
        from app.database.models import Artifact
        from app.orchestration.contracts import GeneratedPlanContract
        from app.database.session import SessionLocal
        
        db = SessionLocal()
        try:
            # Get the run record and update status
            run = db.get(Run, run_id)
            if run is None:
                logger.error(f"Run {run_id} not found")
                return
            
            run.status = "running"
            run.state = {"phase": "running", "step": 1}
            db.add(run)
            db.commit()
            
            logger.info(f"Starting background execution for run {run_id}")
            
            # Reconstruct the plan contract
            plan_snapshot = GeneratedPlanContract(**plan_snapshot_dict)
            
            # Create engine with LLM client
            try:
                llm_client = Qwen3CoderClient()
            except Exception as e:
                logger.warning(f"Could not initialize LLM client: {e}, using mock mode")
                llm_client = None
            
            engine = AutonomousAppEngine(llm_client=llm_client)
            
            # Run the async execution
            outcome = await engine.execute_plan_async(plan_snapshot, run_id)
            
            # Update run with outcome
            run.status = outcome.status.value if hasattr(outcome.status, "value") else str(outcome.status)
            run.output = {"summary": outcome.summary, "project_id": project_id}
            run.state = {
                "phase": "completed",
                "steps": [step.model_dump() for step in plan_snapshot.steps],
            }
            db.add(run)
            db.commit()
            
            # Persist artifacts
            for artifact in outcome.artifacts:
                record = Artifact(
                    run_id=run_id,
                    kind=artifact.kind.value if hasattr(artifact.kind, "value") else str(artifact.kind),
                    path=artifact.path,
                    content=artifact.content,
                    artifact_metadata=artifact.artifact_metadata,
                )
                db.add(record)
            
            db.commit()
            logger.info(f"Background execution completed for run {run_id}: {outcome.status}")
            
        except Exception as e:
            logger.exception(f"Error in background execution: {e}")
            try:
                run = db.get(Run, run_id)
                if run:
                    run.status = "failed"
                    run.output = {"error": str(e)}
                    db.add(run)
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to update run status: {db_err}")
        finally:
            db.close()

    def retry_run(self, run_id: str) -> ProjectExecutionResult:
        run = self.db.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        project = self.db.get(Project, run.project_id)
        plan = self.db.get(Plan, run.plan_id)
        if project is None or plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project plan not found")

        if plan.roadmap:
            plan_snapshot = GeneratedPlanContract(
                project_id=project.id,
                project_name=project.name,
                objective=plan.objective,
                stack=plan.stack,
                steps=[PlanStepContract(**step) for step in plan.roadmap],
            )
        else:
            plan_snapshot = self.engine.build_plan(project.id, project.name, plan.objective)

        return self.execute_project(project, plan, plan_snapshot)
