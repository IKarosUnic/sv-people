"""Optional LLM adapter interface for future local/external model integration.

All core simulation and cognitive mechanics run entirely without an LLM.
This interface provides an optional plug-in point (e.g. for generating
freeform dialogue, rich diary summaries, or LLM-assisted reflection).
"""

from __future__ import annotations

import abc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMAdapter(abc.ABC):
    """Abstract interface for optional language model integration."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend is configured and reachable."""
        raise NotImplementedError

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        """Generate text response from the model."""
        raise NotImplementedError


class NullAdapter(LLMAdapter):
    """Default null adapter — returns empty strings, requires zero external services."""

    def is_available(self) -> bool:
        return False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        return ""


class OllamaAdapter(LLMAdapter):
    """Optional adapter for local Ollama instances (e.g., llama3.2, mistral)."""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        model: str = "llama3.2",
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self._checked: bool = False
        self._available: bool = False

    def is_available(self) -> bool:
        if self._checked:
            return self._available
        try:
            import urllib.request
            req = urllib.request.Request(self.endpoint.replace("/generate", "/tags"))
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                self._available = (resp.status == 200)
        except Exception:
            self._available = False
        self._checked = True
        return self._available

    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        if not self.is_available():
            return ""

        import json
        import urllib.request

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception as ex:
            logger.warning("Ollama call failed: %s", ex)
            return ""
