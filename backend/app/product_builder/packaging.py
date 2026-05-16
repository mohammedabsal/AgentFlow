from __future__ import annotations

import zipfile
from pathlib import Path

from app.core.config import settings


class PackagingService:
    """Create downloadable ZIP archives for generated product workspaces."""

    excluded_dirs = {"node_modules", ".next", "__pycache__", ".pytest_cache", ".git"}

    def __init__(self) -> None:
        self.workspace_root = Path(settings.project_workspace_root).expanduser().resolve()
        self.archive_root = self.workspace_root / "_archives"

    def workspace_for_project(self, project_id: str) -> Path:
        return self.workspace_root / project_id

    def archive_path(self, run_id: str) -> Path:
        return self.archive_root / f"{run_id}.zip"

    def create_zip(self, *, run_id: str, project_id: str) -> Path:
        workspace = self.workspace_for_project(project_id)
        if not workspace.exists():
            raise FileNotFoundError(f"Generated workspace does not exist for project {project_id}")

        self.archive_root.mkdir(parents=True, exist_ok=True)
        archive = self.archive_path(run_id)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for path in workspace.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(workspace)
                if any(part in self.excluded_dirs for part in relative.parts):
                    continue
                zip_file.write(path, relative.as_posix())
        return archive
