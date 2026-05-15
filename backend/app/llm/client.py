from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.core.config import settings
from app.llm.providers import LLMResponse, build_llm_provider

logger = logging.getLogger(__name__)


class Qwen3CoderClient:
    """Compatibility client that routes prompts through the configured provider."""

    def __init__(self) -> None:
        self.provider = build_llm_provider()
        self.model_name = settings.llm_model
        self.temperature = settings.qwen_temperature
        self.max_new_tokens = settings.qwen_max_new_tokens

    def _run(self, coroutine):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        raise RuntimeError("Use the async Qwen3CoderClient methods from an async context.")

    async def a_call_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        response: LLMResponse = await self.provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_message,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=max_tokens or self.max_new_tokens,
        )
        return response.text

    def call_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        return self._run(self.a_call_llm(system_prompt, user_message, temperature, max_tokens))

    async def a_list_installed_models(self) -> dict[str, Any]:
        return await self.provider.list_models()

    def list_installed_models(self) -> dict[str, Any]:
        return self._run(self.a_list_installed_models())

    def generate_plan(self, project_prompt: str) -> dict[str, Any]:
        system_prompt = """You are a production AI software engineering planner.
Return strict JSON only.

Create tasks in this exact autonomous order when appropriate:
prompt_refinement -> planner -> architect -> frontend -> backend -> database -> integration -> testing -> self_healing

Return a JSON object with keys:
{
  "tasks": [
    {"task_id": "1", "agent_role": "prompt_refinement", "description": "...", "input_payload": {}},
    {"task_id": "2", "agent_role": "planner", "description": "...", "input_payload": {}}
  ],
  "agent_assignments": {
    "prompt_refinement": ["1"],
    "planner": ["2"],
    "architect": ["3"],
    "frontend": ["4"],
    "backend": ["5"],
    "database": ["6"],
    "integration": ["7"],
    "testing": ["8"],
    "self_healing": ["9"]
  },
  "estimated_tokens": 8000,
  "plan_version": "2.0"
}"""

        user_message = f"""Turn this product request into an autonomous execution graph:

{project_prompt}

Rules:
- output JSON only
- include clear dependencies
- include a planner step before architecture
- include a self_healing step after testing
- prefer code-generation tasks for frontend, backend, database, integration, and testing
"""

        response_text = self.call_llm(system_prompt, user_message, temperature=0.2)
        return self._parse_json_or_default(response_text, project_prompt)

    async def a_execute_agent_task(
        self,
        agent_role: str,
        task_description: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        agent_prompts: dict[str, dict[str, str]] = {
            "prompt_refinement": {
                "system": "You refine software product requests into precise implementation requirements. Return strict JSON only.",
                "template": """Project Request: {request}

Previous context: {context}

Return JSON keys:
- clarified_requirements
- acceptance_criteria
- risks
- questions
""",
            },
            "planner": {
                "system": "You design the autonomous execution graph. Return strict JSON only.",
                "template": """Request: {request}

Context: {context}

Return JSON keys:
- roadmap
- dependencies
- parallelization_plan
- estimated_duration
""",
            },
            "architect": {
                "system": "You design production software architectures. Return strict JSON only.",
                "template": """Requirements: {requirements}

Context: {context}

Return JSON keys:
- system_architecture
- data_model
- api_contracts
- repo_structure
""",
            },
            "frontend": {
                "system": "You generate production React/Next.js/Tailwind/shadcn code. Return strict JSON only.",
                "template": """Architecture: {architecture}

Requirements: {requirements}

Generate production-ready frontend code. Return JSON keys:
- files: [{{"path": "frontend/src/...", "content": "...", "explanation": "..."}}]
- dependencies
- notes
""",
            },
            "backend": {
                "system": "You generate production FastAPI code, models, and services. Return strict JSON only.",
                "template": """Architecture: {architecture}

Requirements: {requirements}

Generate production-ready backend code. Return JSON keys:
- files: [{{"path": "backend/app/...", "content": "...", "explanation": "..."}}]
- dependencies
- notes
""",
            },
            "database": {
                "system": "You generate database schemas, migrations, and persistence logic. Return strict JSON only.",
                "template": """Architecture: {architecture}

Context: {context}

Return JSON keys:
- files
- migration_notes
- dependencies
""",
            },
            "integration": {
                "system": "You integrate services, environment config, and deployment wiring. Return strict JSON only.",
                "template": """Services: {services}

Context: {context}

Return JSON keys:
- files
- integration_notes
- dependencies
""",
            },
            "testing": {
                "system": "You design tests and validation commands. Return strict JSON only.",
                "template": """Features to test: {features}

Context: {context}

Return JSON keys:
- files
- test_commands
- coverage_goals
""",
            },
            "self_healing": {
                "system": "You repair failing generated code using build errors and diagnostics. Return strict JSON only.",
                "template": """Failure summary: {error}

Context: {context}

Return JSON keys:
- files
- patch_summary
- retry_safe
""",
            },
        }

        agent_config = agent_prompts.get(agent_role, agent_prompts["architect"])
        user_message = agent_config["template"].format(
            request=context.get("request", task_description),
            requirements=context.get("requirements", task_description),
            context=json.dumps(context.get("context", context), indent=2),
            architecture=json.dumps(context.get("architecture", {}), indent=2),
            services=", ".join(context.get("services", [])),
            error=context.get("error", task_description),
            features=json.dumps(context.get("features", []), indent=2),
        )

        response_text = await self.a_call_llm(agent_config["system"], user_message, temperature=0.35)
        return self._parse_json_or_default(response_text, context.get("request", task_description), agent_role)

    def execute_agent_task(
        self,
        agent_role: str,
        task_description: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        return self._run(self.a_execute_agent_task(agent_role, task_description, context))

    def _parse_json_or_default(
        self,
        response_text: str,
        project_prompt: str,
        agent_role: str | None = None,
    ) -> dict[str, Any]:
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                json_str = response_text.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("LLM response was not valid JSON; returning fallback payload.")
            if agent_role:
                return {
                    "agent_role": agent_role,
                    "raw_output": response_text,
                    "status": "needs_review",
                }
            return {
                "tasks": [
                    {"task_id": "1", "agent_role": "prompt_refinement", "description": "Refine requirements", "input_payload": {}},
                    {"task_id": "2", "agent_role": "planner", "description": "Plan execution graph", "input_payload": {}},
                    {"task_id": "3", "agent_role": "architect", "description": "Design system architecture", "input_payload": {}},
                    {"task_id": "4", "agent_role": "frontend", "description": "Generate frontend code", "input_payload": {}},
                    {"task_id": "5", "agent_role": "backend", "description": "Generate backend code", "input_payload": {}},
                    {"task_id": "6", "agent_role": "database", "description": "Generate database schema", "input_payload": {}},
                    {"task_id": "7", "agent_role": "integration", "description": "Integrate systems", "input_payload": {}},
                    {"task_id": "8", "agent_role": "testing", "description": "Validate generated code", "input_payload": {}},
                    {"task_id": "9", "agent_role": "self_healing", "description": "Repair failures", "input_payload": {}},
                ],
                "agent_assignments": {
                    "prompt_refinement": ["1"],
                    "planner": ["2"],
                    "architect": ["3"],
                    "frontend": ["4"],
                    "backend": ["5"],
                    "database": ["6"],
                    "integration": ["7"],
                    "testing": ["8"],
                    "self_healing": ["9"],
                },
                "estimated_tokens": 8000,
                "plan_version": "2.0",
            }