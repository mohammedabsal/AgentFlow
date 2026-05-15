from __future__ import annotations

import asyncio
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.core.config import settings


@dataclass(slots=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


@dataclass(slots=True)
class SandboxFile:
    path: str
    content: str
    explanation: str | None = None


class ProjectSandbox:
    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self.root = Path(settings.project_workspace_root).expanduser().resolve() / project_id

    def ensure(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def write_files(self, files: Iterable[SandboxFile]) -> list[Path]:
        self.ensure()
        written: list[Path] = []
        for file in files:
            target = self.root / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(file.content, encoding="utf-8")
            written.append(target)
        return written

    async def run_command(self, command: str, timeout: float | None = None) -> CommandResult:
        self.ensure()
        started = time.monotonic()
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(self.root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout or settings.llm_request_timeout)
        except asyncio.TimeoutError:
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            return CommandResult(command=command, returncode=124, stdout=stdout_bytes.decode(), stderr=(stderr_bytes.decode() + "\nTimeout exceeded").strip(), duration_ms=int((time.monotonic() - started) * 1000))
        return CommandResult(
            command=command,
            returncode=process.returncode or 0,
            stdout=stdout_bytes.decode(),
            stderr=stderr_bytes.decode(),
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    async def install_dependencies(self) -> CommandResult | None:
        if not (self.root / "package.json").exists():
            return None
        return await self.run_command(settings.npm_install_command, timeout=max(settings.llm_request_timeout, 300.0))

    async def build(self) -> CommandResult | None:
        if not (self.root / "package.json").exists():
            return None
        return await self.run_command(settings.npm_build_command, timeout=max(settings.llm_request_timeout, 300.0))

    async def lint(self) -> CommandResult | None:
        if not (self.root / "package.json").exists():
            return None
        return await self.run_command(settings.npm_lint_command, timeout=max(settings.llm_request_timeout, 300.0))

    def snapshot(self) -> list[str]:
        if not self.root.exists():
            return []
        files: list[str] = []
        for path in self.root.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.root)))
        return sorted(files)