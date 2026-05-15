"""Compatibility shim for older imports.

The system now uses Qwen Coder for all agent orchestration. This module keeps
older import paths working while the rest of the codebase migrates.
"""

from app.llm.qwen_client import Qwen3CoderClient


class AzureOpenAIClient(Qwen3CoderClient):
    """Backward-compatible alias for the Qwen Coder client."""


__all__ = ["AzureOpenAIClient"]
