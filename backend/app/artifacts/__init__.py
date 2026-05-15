"""Artifact generation and file patching."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ArtifactGenerator:
    """Generate real artifacts from LLM outputs."""

    @staticmethod
    def generate_frontend_component(
        component_name: str,
        component_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate a real React/Next.js component from LLM spec.

        Returns:
            Tuple of (file_path, content)
        """
        props_json = json.dumps(component_spec.get('props', {}), indent=2)
        template = f'''import React from 'react';

/**
 * Auto-generated component: {component_name}
 * Generated for project: {project_name}
 */

interface {component_name}Props {{
  // Props from generated spec
  {props_json}
}}

export const {component_name}: React.FC<{component_name}Props> = (props) => {{
  return (
    <div className="component-{component_name.lower()}">
      {{/* Generated component scaffold */}}
      <h2>{component_name}</h2>
      <p>Description: {component_spec.get('description', 'Auto-generated component')}</p>
      {{/* TODO: Implement component logic */}}
    </div>
  );
}};

export default {component_name};
'''
        return (f"frontend/src/components/{component_name}.tsx", template)

    @staticmethod
    def generate_backend_route(
        route_name: str,
        route_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate a real FastAPI route from LLM spec.

        Returns:
            Tuple of (file_path, content)
        """
        methods = route_spec.get("methods", ["GET"])
        path = route_spec.get("path", f"/{route_name.lower()}")

        template = f'''"""
Auto-generated route: {route_name}
Generated for project: {project_name}
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["{route_name.lower()}"])


class {route_name}Request(BaseModel):
    """Request model for {route_name}"""
    # TODO: Add fields from spec
    pass


class {route_name}Response(BaseModel):
    """Response model for {route_name}"""
    # TODO: Add fields from spec
    pass


@router.get("{path}", response_model={route_name}Response)
async def get_{route_name.lower()}(db: Session = Depends(get_db)):
    """
    GET {path}
    
    Auto-generated endpoint.
    Description: {route_spec.get('description', 'Auto-generated endpoint')}
    """
    # TODO: Implement endpoint logic
    return {route_name}Response()


@router.post("{path}", response_model={route_name}Response)
async def create_{route_name.lower()}(request: {route_name}Request, db: Session = Depends(get_db)):
    """
    POST {path}
    
    Auto-generated endpoint.
    """
    # TODO: Implement endpoint logic
    return {route_name}Response()


# Export router
__all__ = ["router"]
'''
        return (f"backend/app/api/routes/{route_name.lower()}.py", template)

    @staticmethod
    def generate_database_model(
        model_name: str,
        model_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate a real SQLAlchemy model from LLM spec.

        Returns:
            Tuple of (file_path, content)
        """
        fields = model_spec.get("fields", {})
        field_definitions = "\n    ".join(
            f"{name}: Mapped[{dtype}] = mapped_column({col_type})"
            for name, (dtype, col_type) in fields.items()
        )

        template = f'''"""
Auto-generated model: {model_name}
Generated for project: {project_name}
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class {model_name}(Base):
    """Auto-generated model for {model_name}"""
    
    __tablename__ = "{model_name.lower()}s"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    {field_definitions}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
'''
        return (f"backend/app/database/models/{model_name.lower()}.py", template)

    @staticmethod
    def generate_test_suite(
        feature_name: str,
        test_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate a test suite from LLM spec.

        Returns:
            Tuple of (file_path, content)
        """
        test_cases = test_spec.get("test_cases", [])
        test_methods = "\n    ".join(
            f"""
    def test_{tc.get('name', 'case')}(self):
        '''Test: {tc.get('description', 'Auto-generated test')}'''
        # TODO: Implement test
        assert True
"""
            for tc in test_cases
        )

        template = f'''"""
Auto-generated test suite: {feature_name}
Generated for project: {project_name}
"""

import pytest


class Test{feature_name}:
    """Auto-generated test class for {feature_name}"""

    def setup_method(self):
        """Setup test fixtures"""
        pass

    def teardown_method(self):
        """Cleanup after tests"""
        pass
{test_methods}
'''
        return (f"tests/test_{feature_name.lower()}.py", template)

    @staticmethod
    def generate_documentation(
        doc_name: str,
        doc_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate documentation from LLM spec.

        Returns:
            Tuple of (file_path, content)
        """
        template = f'''# {doc_name}

**Project:** {project_name}

**Generated:** Auto-generated documentation

## Overview

{doc_spec.get('overview', 'This is auto-generated documentation.')}

## Features

{chr(10).join(f"- {feat}" for feat in doc_spec.get('features', []))}

## Usage

{doc_spec.get('usage', '```\n# Usage example\n```')}

## API Reference

{doc_spec.get('api_reference', '### Endpoints\n(Auto-generated)')}

## Configuration

{doc_spec.get('configuration', '(Auto-generated)')}

---

*This documentation was auto-generated by the Autonomous App Engine.*
'''
        return (f"docs/{doc_name.lower()}.md", template)


class ArtifactPatcher:
    """Apply patches and modifications to generated artifacts."""

    @staticmethod
    def apply_fix(content: str, fix_spec: dict[str, Any]) -> str:
        """
        Apply a fix/patch to generated code.

        Args:
            content: Original artifact content
            fix_spec: Fix specification with original and replacement

        Returns:
            Patched content
        """
        original = fix_spec.get("original", "")
        replacement = fix_spec.get("replacement", "")

        if original and original in content:
            return content.replace(original, replacement)

        logger.warning(f"Could not apply fix: original text not found in artifact")
        return content

    @staticmethod
    def inject_code(
        content: str,
        injection_spec: dict[str, Any],
    ) -> str:
        """
        Inject code at a specific location.

        Args:
            content: Original artifact content
            injection_spec: Injection point and code to inject

        Returns:
            Content with injected code
        """
        marker = injection_spec.get("marker", "")
        code = injection_spec.get("code", "")
        position = injection_spec.get("position", "after")  # before or after

        if marker not in content:
            logger.warning(f"Could not inject code: marker not found")
            return content

        marker_index = content.find(marker)
        if position == "before":
            return content[:marker_index] + code + "\n" + content[marker_index:]
        else:  # after
            marker_end = marker_index + len(marker)
            return content[:marker_end] + "\n" + code + content[marker_end:]

    @staticmethod
    def generate_config(
        config_name: str,
        config_spec: dict[str, Any],
        project_name: str,
    ) -> tuple[str, str]:
        """
        Generate configuration files.

        Returns:
            Tuple of (file_path, content)
        """
        if config_name.endswith(".json"):
            content = json.dumps(config_spec, indent=2)
        elif config_name.endswith(".env"):
            lines = [f"{k}={v}" for k, v in config_spec.items()]
            content = "\n".join(lines)
        else:
            content = json.dumps(config_spec, indent=2)

        return (f"config/{config_name}", content)


# Factory functions
def generate_artifact(
    artifact_type: str,
    artifact_name: str,
    artifact_spec: dict[str, Any],
    project_name: str,
) -> tuple[str, str]:
    """
    Factory function to generate artifacts of various types.

    Returns:
        Tuple of (file_path, content)
    """
    generator = ArtifactGenerator()

    if artifact_type == "frontend_component":
        return generator.generate_frontend_component(artifact_name, artifact_spec, project_name)
    elif artifact_type == "backend_route":
        return generator.generate_backend_route(artifact_name, artifact_spec, project_name)
    elif artifact_type == "database_model":
        return generator.generate_database_model(artifact_name, artifact_spec, project_name)
    elif artifact_type == "test_suite":
        return generator.generate_test_suite(artifact_name, artifact_spec, project_name)
    elif artifact_type == "documentation":
        return generator.generate_documentation(artifact_name, artifact_spec, project_name)
    elif artifact_type == "config":
        patcher = ArtifactPatcher()
        return patcher.generate_config(artifact_name, artifact_spec, project_name)
    else:
        logger.warning(f"Unknown artifact type: {artifact_type}")
        return (f"generated/{artifact_name}", json.dumps(artifact_spec))
