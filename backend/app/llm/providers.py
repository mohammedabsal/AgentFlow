from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse: ...

    async def stream(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]: ...

    async def list_models(self) -> dict[str, Any]: ...


class BaseProvider:
    name = "base"

    def __init__(self, *, model: str, base_url: str, api_key: str | None = None) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = settings.llm_request_timeout
        self.max_retries = settings.llm_max_retries

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request_json(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
                    logger.debug(f"Provider request attempt {attempt + 1}/{self.max_retries + 1}: {method} {url}")
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, dict):
                        return payload
                    return {"data": payload}
            except (httpx.HTTPError, json.JSONDecodeError, httpx.ReadTimeout) as exc:
                last_error = exc
                logger.warning(f"Provider request failed (attempt {attempt + 1}/{self.max_retries + 1}): {type(exc).__name__}: {exc}")
                if attempt == self.max_retries:
                    logger.error(f"Provider request exhausted all retries: {exc}")
                    raise
                wait_time = 0.5 * (2 ** attempt)  # Exponential backoff: 0.5s, 1s, 2s, etc.
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        raise RuntimeError(str(last_error) if last_error else "Unknown provider error")

    async def _stream_lines(self, method: str, url: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
                    logger.debug(f"Provider stream attempt {attempt + 1}/{self.max_retries + 1}: {method} {url}")
                    async with client.stream(method, url, **kwargs) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                yield line
                        return
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning(f"Provider stream failed (attempt {attempt + 1}/{self.max_retries + 1}): {type(exc).__name__}: {exc}")
                if attempt == self.max_retries:
                    logger.error(f"Provider stream exhausted all retries: {exc}")
                    raise
                wait_time = 0.5 * (2 ** attempt)
                logger.info(f"Retrying stream in {wait_time}s...")
                await asyncio.sleep(wait_time)
        raise RuntimeError(str(last_error) if last_error else "Unknown provider stream error")


class OllamaProvider(BaseProvider):
    name = "ollama"

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        response = await self._request_json("POST", f"{self.base_url}/api/generate", json=payload)
        return LLMResponse(
            text=str(response.get("response", "")).strip(),
            provider=self.name,
            model=self.model,
            usage={"prompt_tokens": int(response.get("prompt_eval_count", 0) or 0), "completion_tokens": int(response.get("eval_count", 0) or 0)},
            raw=response,
        )

    async def stream(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async for line in self._stream_lines("POST", f"{self.base_url}/api/generate", json=payload):
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            response = chunk.get("response")
            if response:
                yield str(response)

    async def list_models(self) -> dict[str, Any]:
        return await self._request_json("GET", f"{self.base_url}/api/tags")


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    async def generate(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = await self._request_json("POST", f"{self.base_url}/chat/completions", json=payload)
        text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(text=str(text).strip(), provider=self.name, model=self.model, raw=response)

    async def stream(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async for line in self._stream_lines("POST", f"{self.base_url}/chat/completions", json=payload):
            if line.startswith("data: "):
                line = line.removeprefix("data: ").strip()
            if line == "[DONE]":
                break
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            if delta:
                yield str(delta)

    async def list_models(self) -> dict[str, Any]:
        return {"provider": self.name, "models": [self.model]}


class GroqProvider(OpenRouterProvider):
    name = "groq"


class GeminiProvider(BaseProvider):
    name = "gemini"

    async def generate(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"System: {system_prompt}\n\nUser: {user_prompt}"}]}
            ],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        response = await self._request_json(
            "POST",
            f"{self.base_url}/models/{self.model}:generateContent",
            params={"key": self.api_key or ""},
            json=payload,
        )
        candidates = response.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts)
        return LLMResponse(text=text.strip(), provider=self.name, model=self.model, raw=response)

    async def stream(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.text:
            yield response.text

    async def list_models(self) -> dict[str, Any]:
        return {"provider": self.name, "models": [self.model]}


def build_llm_provider() -> LLMProvider:
    provider_name = settings.llm_provider.lower().strip()
    if provider_name == "openrouter":
        return OpenRouterProvider(model=settings.openrouter_model, base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)
    if provider_name == "groq":
        return GroqProvider(model=settings.groq_model, base_url=settings.groq_base_url, api_key=settings.groq_api_key)
    if provider_name == "gemini":
        return GeminiProvider(model=settings.gemini_model, base_url=settings.gemini_base_url, api_key=settings.gemini_api_key)
    return OllamaProvider(model=settings.ollama_model or settings.llm_model, base_url=settings.ollama_base_url)