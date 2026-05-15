from app.database.models import Execution
from app.database.session import SessionLocal
from app.observability.event_store import execution_events
from app.queues.celery_app import celery_app
from app.runtime.executor import WorkflowExecutor
from app.runtime.state import ExecutionState


@celery_app.task(name="workflow.execute")
def execute_workflow(execution_id: str, workflow_id: str, input_payload: dict[str, object]) -> dict[str, object]:
    db = SessionLocal()
    try:
        execution = db.get(Execution, execution_id)
        if execution is None:
            execution_events.append(execution_id, "execution.missing", {"workflow_id": workflow_id})
            return {"execution_id": execution_id, "status": "missing"}

        execution.status = "running"
        execution.state = {"step": 1, "phase": "running"}
        db.add(execution)
        db.commit()
        db.refresh(execution)
        execution_events.append(execution_id, "execution.started", {"workflow_id": workflow_id, "status": execution.status})

        executor = WorkflowExecutor()
        state = ExecutionState(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running",
            outputs=input_payload,
        )
        result = executor.start(state)

        execution.status = "completed"
        execution.output = {"result": "completed", "input": input_payload}
        execution.state = {
            "step": state.step_count,
            "phase": "completed",
            "history": state.history,
        }
        db.add(execution)
        db.commit()
        db.refresh(execution)
        execution_events.append(execution_id, "execution.completed", {"status": execution.status, "output": execution.output})
        return {**result, "status": execution.status, "output": execution.output}
    finally:
        db.close()


@celery_app.task(name="project.execute_async", bind=True)
def execute_project_task(self, project_id: str, plan_id: str, run_id: str, plan_snapshot_dict: dict) -> dict[str, object]:
    """Celery task to execute a project plan asynchronously.
    
    This runs in a background worker and can handle long-running LLM operations.
    """
    import asyncio
    import logging
    from app.database.models import Artifact, Run
    from app.orchestration.contracts import GeneratedPlanContract
    from app.orchestration.engine import AutonomousAppEngine
    from app.llm.client import Qwen3CoderClient
    from app.database.session import SessionLocal
    
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        # Get the run record and update status to running
        run = db.get(Run, run_id)
        if run is None:
            logger.error(f"Run {run_id} not found")
            return {"run_id": run_id, "status": "failed", "error": "Run not found"}
        
        run.status = "running"
        run.state = {"phase": "running", "step": 1}
        db.add(run)
        db.commit()
        
        logger.info(f"Starting execution for run {run_id} with plan {plan_id}")
        
        # Reconstruct the plan contract
        plan_snapshot = GeneratedPlanContract(**plan_snapshot_dict)
        
        # Create engine with LLM client
        try:
            llm_client = Qwen3CoderClient()
        except Exception as e:
            logger.warning(f"Could not initialize LLM client: {e}, using mock mode")
            llm_client = None
        
        engine = AutonomousAppEngine(llm_client=llm_client)
        
        # Run the async execution. If an event loop is already running (e.g. eager Celery
        # execution inside an async server), run the coroutine in a dedicated thread
        # with its own event loop to avoid "asyncio.run() cannot be called from a running event loop".
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in this thread — safe to use asyncio.run
            outcome = asyncio.run(engine.execute_plan_async(plan_snapshot, run_id))
        else:
            # Running loop detected — execute in a new thread with its own loop
            import concurrent.futures

            def _run_in_thread():
                return asyncio.new_event_loop().run_until_complete(
                    engine.execute_plan_async(plan_snapshot, run_id)
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_run_in_thread)
                outcome = future.result()
        
        # Update run with outcome
        run.status = outcome.status
        run.output = {"summary": outcome.summary, "project_id": project_id}
        run.state = {
            "phase": "completed",
            "steps": [step.model_dump() for step in plan_snapshot.steps],
        }
        db.add(run)
        db.commit()
        
        # Persist artifacts
        artifacts: list[Artifact] = []
        for artifact in outcome.artifacts:
            record = Artifact(
                run_id=run_id,
                kind=artifact.kind,
                path=artifact.path,
                content=artifact.content,
                artifact_metadata=artifact.artifact_metadata,
            )
            db.add(record)
            artifacts.append(record)
        
        db.commit()
        logger.info(f"Execution completed for run {run_id}: {outcome.status}")
        
        return {
            "run_id": run_id,
            "status": outcome.status,
            "summary": outcome.summary,
            "artifact_count": len(artifacts),
        }
    except Exception as e:
        logger.exception(f"Error executing project: {e}")
        try:
            run = db.get(Run, run_id)
            if run:
                run.status = "failed"
                run.output = {"error": str(e)}
                db.add(run)
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update run status: {db_err}")
        
        return {"run_id": run_id, "status": "failed", "error": str(e)}
    finally:
        db.close()
