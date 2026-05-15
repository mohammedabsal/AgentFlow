"""
Workspace execution engine for running code in isolated Docker containers.

Handles:
- Docker workspace creation
- File management
- Code execution (build, test, install)
- Output capture
- Error recovery
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.orchestration.contracts import (
    ExecutionStatus,
    WorkspaceExecutionResult,
    WorkspaceMetadata,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceConfig:
    """Configuration for workspace execution."""

    workspace_id: str
    project_id: str
    run_id: str
    mount_path: str
    docker_image: str = "ubuntu:22.04"
    exposed_ports: list[int] = None
    env_vars: dict[str, str] = None
    timeout_seconds: int = 3600

    def __post_init__(self):
        if self.exposed_ports is None:
            self.exposed_ports = []
        if self.env_vars is None:
            self.env_vars = {}


class WorkspaceManager:
    """Manage Docker workspaces for code execution."""

    def __init__(self, base_mount_path: Optional[str] = None):
        """Initialize workspace manager."""
        self.base_mount_path = base_mount_path or "/tmp/agentflow-workspaces"
        self.active_workspaces: dict[str, WorkspaceConfig] = {}
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """Ensure base mount path exists."""
        Path(self.base_mount_path).mkdir(parents=True, exist_ok=True)

    async def create_workspace(
        self,
        project_id: str,
        run_id: str,
        docker_image: str = "ubuntu:22.04",
    ) -> WorkspaceMetadata:
        """Create a new workspace."""
        workspace_id = str(uuid.uuid4())
        mount_path = os.path.join(self.base_mount_path, workspace_id)

        # Create workspace directory
        Path(mount_path).mkdir(parents=True, exist_ok=True)

        config = WorkspaceConfig(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            mount_path=mount_path,
            docker_image=docker_image,
        )

        self.active_workspaces[workspace_id] = config

        metadata = WorkspaceMetadata(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            mount_path=mount_path,
            docker_image=docker_image,
            status="created",
        )

        logger.info(f"Created workspace: {workspace_id}")
        return metadata

    async def write_file(
        self,
        workspace_id: str,
        file_path: str,
        content: str,
    ) -> bool:
        """Write file to workspace."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            logger.error(f"Workspace not found: {workspace_id}")
            return False

        full_path = Path(config.mount_path) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            full_path.write_text(content, encoding="utf-8")
            logger.debug(f"Wrote file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False

    async def read_file(
        self,
        workspace_id: str,
        file_path: str,
    ) -> Optional[str]:
        """Read file from workspace."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            return None

        full_path = Path(config.mount_path) / file_path
        if not full_path.exists():
            return None

        try:
            return full_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    async def execute_command(
        self,
        workspace_id: str,
        command: str,
        timeout_seconds: int = 300,
    ) -> WorkspaceExecutionResult:
        """Execute command in workspace."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            return WorkspaceExecutionResult(
                execution_id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                command=command,
                status=ExecutionStatus.FAILED,
                stderr="Workspace not found",
            )

        execution_id = str(uuid.uuid4())

        try:
            # Execute command in the workspace directory
            result = await self._run_command(
                command=command,
                cwd=config.mount_path,
                timeout_seconds=timeout_seconds,
            )

            return WorkspaceExecutionResult(
                execution_id=execution_id,
                workspace_id=workspace_id,
                command=command,
                status=result["status"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                exit_code=result["exit_code"],
                duration_ms=result["duration_ms"],
            )

        except asyncio.TimeoutError:
            return WorkspaceExecutionResult(
                execution_id=execution_id,
                workspace_id=workspace_id,
                command=command,
                status=ExecutionStatus.FAILED,
                stderr="Command execution timed out",
                exit_code=124,
                duration_ms=timeout_seconds * 1000,
            )

        except Exception as e:
            return WorkspaceExecutionResult(
                execution_id=execution_id,
                workspace_id=workspace_id,
                command=command,
                status=ExecutionStatus.FAILED,
                stderr=str(e),
                exit_code=1,
            )

    async def _run_command(
        self,
        command: str,
        cwd: str,
        timeout_seconds: int = 300,
    ) -> dict:
        """Run command and capture output."""
        import time

        start_time = time.time()

        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                raise

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "status": ExecutionStatus.COMPLETED if process.returncode == 0 else ExecutionStatus.FAILED,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": process.returncode,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    async def install_dependencies(
        self,
        workspace_id: str,
        package_manager: str = "pip",
        requirements_file: str = "requirements.txt",
    ) -> WorkspaceExecutionResult:
        """Install dependencies in workspace."""
        if package_manager == "pip":
            command = f"pip install -r {requirements_file}"
        elif package_manager == "npm":
            command = "npm install"
        elif package_manager == "yarn":
            command = "yarn install"
        else:
            return WorkspaceExecutionResult(
                execution_id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                command="",
                status=ExecutionStatus.FAILED,
                stderr=f"Unknown package manager: {package_manager}",
            )

        return await self.execute_command(workspace_id, command, timeout_seconds=600)

    async def run_tests(
        self,
        workspace_id: str,
        test_framework: str = "pytest",
    ) -> WorkspaceExecutionResult:
        """Run tests in workspace."""
        if test_framework == "pytest":
            command = "pytest -v --tb=short"
        elif test_framework == "jest":
            command = "npm test"
        elif test_framework == "go":
            command = "go test ./..."
        else:
            command = test_framework

        return await self.execute_command(workspace_id, command, timeout_seconds=300)

    async def build_project(
        self,
        workspace_id: str,
        build_command: str = "npm run build",
    ) -> WorkspaceExecutionResult:
        """Build project in workspace."""
        return await self.execute_command(workspace_id, build_command, timeout_seconds=600)

    async def cleanup_workspace(self, workspace_id: str) -> bool:
        """Delete workspace and all contents."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            return False

        try:
            import shutil

            shutil.rmtree(config.mount_path)
            del self.active_workspaces[workspace_id]
            logger.info(f"Cleaned up workspace: {workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup workspace {workspace_id}: {e}")
            return False

    async def get_workspace_info(self, workspace_id: str) -> Optional[dict]:
        """Get workspace information."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            return None

        workspace_path = Path(config.mount_path)
        file_count = sum(1 for _ in workspace_path.rglob("*") if _.is_file())
        total_size = sum(f.stat().st_size for f in workspace_path.rglob("*") if f.is_file())

        return {
            "workspace_id": workspace_id,
            "project_id": config.project_id,
            "run_id": config.run_id,
            "mount_path": config.mount_path,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "docker_image": config.docker_image,
        }

    def list_workspace_files(self, workspace_id: str) -> Optional[list[str]]:
        """List all files in workspace."""
        config = self.active_workspaces.get(workspace_id)
        if not config:
            return None

        workspace_path = Path(config.mount_path)
        files = []

        for file_path in workspace_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(workspace_path)
                files.append(str(rel_path))

        return sorted(files)


# Global workspace manager instance
workspace_manager = WorkspaceManager()
