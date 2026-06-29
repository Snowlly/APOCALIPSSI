"""Services LLM — abstraction Ollama / Mock + factory."""

from .factory import get_llm_client

__all__ = ["get_llm_client"]
