"""
LangGraph-based orchestration engine for multi-agent autonomous workflows.

Handles:
- Agent task scheduling and execution
- Parallel execution with dependency tracking
- State management across agents
- Error recovery and self-healing loops
- Real-time WebSocket streaming
- Workspace execution and artifact management
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from app.agents.multi_agent_system import (
    AgentContext,
    AgentTaskInput,
    AgentTaskOutput,
    get_agent,
)
from app.llm.client import Qwen3CoderClient
from app.orchestration.contracts import (
    AgentRole,
    ExecutionLogEntry,
    ExecutionPlanContract,
    ExecutionStatus,
    ExecutionStreamMessage,
    RunOutcomeContract,
    SelfHealingLoopContract,
    TaskExecutionState,
    WorkspaceExecutionResult,
)

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """
    LangGraph-inspired orchestration engine for autonomous multi-agent workflows.
    
    Manages:
    - Agent coordination
    - Task scheduling
    - State management
    - Error recovery
    - Real-time streaming
    """

    def __init__(self, llm_client: Optional[Qwen3CoderClient] = None):
        """Initialize orchestration engine."""
        self.llm_client = llm_client or Qwen3CoderClient()
        self.active_executions: dict[str, ExecutionRuntime] = {}

    async def create_execution_plan(
        self,
        project_id: str,
        project_name: str,
        user_prompt: str,
    ) -> ExecutionPlanContract:
        """Create detailed execution plan from user prompt."""
        plan = ExecutionPlanContract(
            plan_id=str(uuid.uuid4()),
            project_id=project_id,
            project_name=project_name,
            user_prompt=user_prompt,
        )

        # Get refined prompt from Prompt Refiner Agent
        context = AgentContext(
            execution_id=plan.plan_id,
            project_id=project_id,
            project_name=project_name,
            user_prompt=user_prompt,
        )

        try:
            refiner = get_agent(AgentRole.PROMPT_REFINER, self.llm_client)
            task_input = AgentTaskInput(
                task_id="refine-prompt",
                agent=AgentRole.PROMPT_REFINER,
                context=context,
                requirements="Refine the user prompt",
            )
            result = await refiner.execute(task_input)
            plan.refined_prompt = context.refined_prompt

            logger.info(f"Created execution plan {plan.plan_id}")

        except Exception as e:
            logger.error(f"Failed to create execution plan: {e}")
            plan.refined_prompt = user_prompt

        return plan

    async def execute_workflow(
        self,
        project_id: str,
        project_name: str,
        user_prompt: str,
        execution_id: Optional[str] = None,
        on_message: Optional[callable] = None,
    ) -> RunOutcomeContract:
        """Execute complete autonomous workflow."""
        execution_id = execution_id or str(uuid.uuid4())
        runtime = ExecutionRuntime(
            execution_id=execution_id,
            project_id=project_id,
            project_name=project_name,
            user_prompt=user_prompt,
            llm_client=self.llm_client,
            on_message=on_message,
        )

        self.active_executions[execution_id] = runtime

        try:
            outcome = await runtime.run()
            return outcome

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise

    async def get_execution_status(self, execution_id: str) -> Optional[dict]:
        """Get current execution status."""
        runtime = self.active_executions.get(execution_id)
        if not runtime:
            return None

        return {
            "execution_id": execution_id,
            "status": runtime.status.value,
            "current_task": runtime.current_task,
            "completed_tasks": runtime.completed_tasks,
            "logs": [log.model_dump() for log in runtime.logs[-20:]],  # Last 20 logs
            "progress": f"{len(runtime.completed_tasks)}/{len(runtime.planned_tasks)}",
        }

    def stop_execution(self, execution_id: str) -> bool:
        """Stop an ongoing execution."""
        runtime = self.active_executions.get(execution_id)
        if runtime:
            runtime.status = ExecutionStatus.CANCELLED
            return True
        return False


class ExecutionRuntime:
    """
    Runtime for executing a single autonomous workflow.
    
    Manages:
    - Agent sequencing
    - Parallel task execution
    - State management
    - Error handling
    - WebSocket streaming
    """

    def __init__(
        self,
        execution_id: str,
        project_id: str,
        project_name: str,
        user_prompt: str,
        llm_client: Qwen3CoderClient,
        on_message: Optional[callable] = None,
    ):
        """Initialize runtime."""
        self.execution_id = execution_id
        self.project_id = project_id
        self.project_name = project_name
        self.user_prompt = user_prompt
        self.llm_client = llm_client
        self.on_message = on_message

        self.context = AgentContext(
            execution_id=execution_id,
            project_id=project_id,
            project_name=project_name,
            user_prompt=user_prompt,
        )

        self.status = ExecutionStatus.PENDING
        self.planned_tasks: list[tuple[AgentRole, str]] = []
        self.completed_tasks: list[str] = []
        self.current_task: Optional[str] = None
        self.logs: list[ExecutionLogEntry] = []
        self.task_results: dict[str, TaskExecutionState] = {}
        self.self_healing_loops: list[SelfHealingLoopContract] = []

    async def run(self) -> RunOutcomeContract:
        """Execute the complete workflow."""
        self.status = ExecutionStatus.RUNNING
        self._log("info", "system", "Starting autonomous workflow execution")

        try:
            # Phase 1: Prompt Refinement
            await self._execute_phase(
                "Prompt Refinement",
                [(AgentRole.PROMPT_REFINER, "Refine prompt into structured requirements")],
            )

            # Phase 2: Research & Analysis
            await self._execute_phase(
                "Research",
                [(AgentRole.RESEARCH, "Research tech landscape and best practices")],
            )

            # Phase 3: Planning
            await self._execute_phase(
                "Planning",
                [(AgentRole.PLANNER, "Create execution plan with task dependencies")],
            )

            # Phase 4: Architecture Design
            await self._execute_phase(
                "Architecture",
                [(AgentRole.ARCHITECT, "Design system architecture")],
            )

            # Phase 5: Parallel Code Generation
            await self._execute_phase(
                "Code Generation",
                [
                    (AgentRole.FRONTEND, "Generate frontend code"),
                    (AgentRole.BACKEND, "Generate backend code"),
                    (AgentRole.DATABASE, "Design database schema"),
                    (AgentRole.API, "Design API specification"),
                    (AgentRole.DEVOPS, "Create deployment configs"),
                ],
                parallel=True,
            )

            # Phase 6: Testing
            await self._execute_phase(
                "Testing",
                [(AgentRole.TESTING, "Generate comprehensive tests")],
            )

            # Phase 7: Self-Healing Loop (if errors detected)
            if self.context.execution_errors:
                await self._execute_self_healing_loop()

            self.status = ExecutionStatus.COMPLETED
            self._log("info", "system", "Workflow execution completed successfully")

        except Exception as e:
            self.status = ExecutionStatus.FAILED
            self._log("error", "system", f"Workflow execution failed: {e}")
            self.context.execution_errors.append(str(e))

        return self._build_outcome()

    async def _execute_phase(
        self,
        phase_name: str,
        tasks: list[tuple[AgentRole, str]],
        parallel: bool = False,
    ) -> None:
        """Execute a phase with one or more tasks."""
        self._log("info", "system", f"Starting phase: {phase_name}")

        if parallel:
            # Execute tasks in parallel
            await self._execute_parallel_tasks(tasks)
        else:
            # Execute tasks sequentially
            for agent_role, description in tasks:
                await self._execute_task(agent_role, description)

        self._log("info", "system", f"Completed phase: {phase_name}")

    async def _execute_parallel_tasks(self, tasks: list[tuple[AgentRole, str]]) -> None:
        """Execute multiple tasks in parallel."""
        coroutines = [self._execute_task(agent, desc) for agent, desc in tasks]
        await asyncio.gather(*coroutines, return_exceptions=True)

    async def _execute_task(self, agent_role: AgentRole, description: str) -> None:
        """Execute a single agent task."""
        if self.status == ExecutionStatus.CANCELLED:
            return

        task_id = f"{agent_role.value}-{uuid.uuid4().hex[:8]}"
        self.current_task = task_id
        self.planned_tasks.append((agent_role, task_id))

        self._log("info", agent_role.value, f"Starting task: {description}")

        try:
            # Create agent instance
            agent = get_agent(agent_role, self.llm_client)

            # Prepare task input
            task_input = AgentTaskInput(
                task_id=task_id,
                agent=agent_role,
                context=self.context,
                requirements=description,
                previous_outputs=list(self.context.generated_artifacts.values()),
            )

            # Execute agent
            output = await agent.execute(task_input)

            # Record results
            self.task_results[task_id] = TaskExecutionState(
                task_id=task_id,
                execution_id=self.execution_id,
                status=output.status,
                agent=agent_role,
                output_artifacts=output.artifacts,
                logs=self.logs.copy(),
                tokens_used=output.tokens_used,
            )

            # Store artifacts
            for artifact in output.artifacts:
                self.context.generated_artifacts[artifact.path] = artifact

            # Log task completion
            self.completed_tasks.append(task_id)
            self._log("info", agent_role.value, f"Task completed: {description}")

            # Stream artifacts
            for artifact in output.artifacts:
                await self._stream_message(
                    type="artifact",
                    agent=agent_role,
                    content=f"Generated: {artifact.path}",
                    metadata={"artifact_id": artifact.artifact_id, "path": artifact.path},
                )

        except Exception as e:
            self._log("error", agent_role.value, f"Task failed: {str(e)}")
            self.context.execution_errors.append(f"{agent_role.value}: {str(e)}")
            self.task_results[task_id] = TaskExecutionState(
                task_id=task_id,
                execution_id=self.execution_id,
                status=ExecutionStatus.FAILED,
                agent=agent_role,
                errors=[str(e)],
            )

    async def _execute_self_healing_loop(self) -> None:
        """Execute self-healing loop to fix errors."""
        if not self.context.execution_errors:
            return

        self._log("info", "system", "Starting self-healing loop")

        try:
            healing_agent = get_agent(AgentRole.SELF_HEALING, self.llm_client)

            task_input = AgentTaskInput(
                task_id=f"self-heal-{uuid.uuid4().hex[:8]}",
                agent=AgentRole.SELF_HEALING,
                context=self.context,
                requirements="Analyze and fix execution errors",
                previous_outputs=list(self.context.generated_artifacts.values()),
            )

            output = await healing_agent.execute(task_input)

            # Record healing loop
            healing_loop = SelfHealingLoopContract(
                loop_id=task_input.task_id,
                execution_id=self.execution_id,
                iteration=len(self.self_healing_loops) + 1,
                error_analysis={
                    "error_id": str(uuid.uuid4()),
                    "error_message": "; ".join(self.context.execution_errors),
                    "error_type": "execution_error",
                    "context": "Multi-agent workflow execution",
                    "severity": "warning",
                    "suggested_fix": self.context.shared_memory.get("fixes", ""),
                },
                resolved=output.status == ExecutionStatus.COMPLETED,
            )

            self.self_healing_loops.append(healing_loop)
            self._log("info", "system", "Self-healing loop completed")

        except Exception as e:
            self._log("error", "system", f"Self-healing failed: {e}")

    def _log(self, level: str, source: str, message: str) -> None:
        """Add log entry and stream it."""
        entry = ExecutionLogEntry(level=level, source=source, message=message)
        self.logs.append(entry)

        # Stream log message
        asyncio.create_task(
            self._stream_message(
                type="log",
                content=message,
                metadata={"level": level, "source": source},
            )
        )

    async def _stream_message(
        self,
        type: str,
        content: str,
        agent: Optional[AgentRole] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Stream message via WebSocket."""
        if not self.on_message:
            return

        message = ExecutionStreamMessage(
            type=type,
            execution_id=self.execution_id,
            agent=agent,
            content=content,
            metadata=metadata or {},
        )

        try:
            if asyncio.iscoroutinefunction(self.on_message):
                await self.on_message(message)
            else:
                self.on_message(message)
        except Exception as e:
            logger.warning(f"Failed to stream message: {e}")

    def _build_outcome(self) -> RunOutcomeContract:
        """Build final execution outcome."""
        return RunOutcomeContract(
            run_id=str(uuid.uuid4()),
            execution_id=self.execution_id,
            project_id=self.project_id,
            status=self.status,
            summary=f"Execution {'completed' if self.status == ExecutionStatus.COMPLETED else 'failed'}. "
            f"Completed {len(self.completed_tasks)} tasks, encountered {len(self.context.execution_errors)} errors.",
            artifacts=list(self.context.generated_artifacts.values()),
            logs=self.logs,
            errors=self.context.execution_errors,
            self_healing_loops=self.self_healing_loops,
            task_results=self.task_results,
            total_tokens_used=sum(t.tokens_used for t in self.task_results.values()),
        )
