"""LLM Integration Layer Interfaces (Abstract, Optional, Disabled).

Provides a clean architectural blueprint for future AI integrations (OpenAI, Gemini,
local Ollama, vLLM, etc.) without requiring external packages, network connectivity,
or paid API dependencies in Phase 0.3.

All components remain disabled by default.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PromptContext:
    """Structured context gathered from simulation entities to prompt a future model."""

    agent_id: str
    agent_name: str
    current_tick: int
    situation: str
    memories: list[str] = field(default_factory=list)
    active_goals: list[str] = field(default_factory=list)
    emotional_state: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Structured validation output from an AI model invocation."""

    raw_text: str
    parsed_action: Optional[str] = None
    confidence: float = 0.0
    tokens_used: int = 0
    is_valid: bool = False
    validation_errors: list[str] = field(default_factory=list)


class ModelProviderInterface(abc.ABC):
    """Abstract interface for model providers."""

    @abc.abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available locally or remotely."""
        raise NotImplementedError

    @abc.abstractmethod
    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Synchronously request completion text."""
        raise NotImplementedError


class LocalModelAdapter(ModelProviderInterface):
    """Placeholder adapter for local inference engines (Ollama, llama.cpp)."""

    def __init__(self, endpoint: str = "http://localhost:11434", model_name: str = "mock-disabled") -> None:
        self.endpoint = endpoint
        self.model_name = model_name
        self.enabled = False

    def name(self) -> str:
        return f"LocalModelAdapter({self.model_name})"

    def is_available(self) -> bool:
        # Strictly disabled in Phase 0.3
        return False

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        return ""


class ExternalAPIAdapter(ModelProviderInterface):
    """Placeholder adapter for cloud models (Gemini, OpenAI, etc.)."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "mock-disabled") -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.enabled = False

    def name(self) -> str:
        return f"ExternalAPIAdapter({self.model_name})"

    def is_available(self) -> bool:
        # Strictly disabled in Phase 0.3
        return False

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        return ""


class ContextBuilder:
    """Builds clean, token-efficient prompt contexts from internal simulation state."""

    @staticmethod
    def build_from_human(human: Any, situation_summary: str, current_tick: int) -> PromptContext:
        """Convert a SyntheticHuman instance into a clean PromptContext."""
        memories = [m.summary for m in human.memory.episodic.get_recent(3)]
        goals = [g.description for g in human.autonomy.get_active_goals()]
        emotions = {
            e.value if hasattr(e, "value") else str(e): st.intensity
            for e, st in getattr(human.emotions.profile, "active_emotions", {}).items()
            if st.intensity > 0.05
        }
        return PromptContext(
            agent_id=str(human.uid),
            agent_name=human.name,
            current_tick=current_tick,
            situation=situation_summary,
            memories=memories,
            active_goals=goals,
            emotional_state=emotions,
        )


class ResponseValidator:
    """Validates that future LLM outputs conform to simulation constraints and schema."""

    @staticmethod
    def validate_action(response_text: str, allowed_actions: list[str]) -> ModelResponse:
        """Verify whether generated text specifies a permissible action."""
        clean = response_text.strip().lower()
        for act in allowed_actions:
            if act.lower() in clean:
                return ModelResponse(
                    raw_text=response_text,
                    parsed_action=act,
                    confidence=0.9,
                    is_valid=True,
                )
        return ModelResponse(
            raw_text=response_text,
            is_valid=False,
            validation_errors=["Action not found in allowed actions set."],
        )


class ResourceManager:
    """Enforces rate limiting, token budgets, and concurrency controls for future AI calls."""

    def __init__(self, max_calls_per_minute: int = 60, max_tokens_per_hour: int = 100000) -> None:
        self.max_calls_per_minute = max_calls_per_minute
        self.max_tokens_per_hour = max_tokens_per_hour
        self.call_count = 0
        self.token_count = 0

    def can_request(self) -> bool:
        """Determine if request budget allows an AI query."""
        return False  # Disabled in Phase 0.3
