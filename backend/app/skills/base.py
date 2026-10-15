"""Skill abstract base class — each skill = system_prompt + tools + schema."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SkillResult:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    confidence: "ConfidenceMarker | None" = None


class BaseSkill(ABC):
    """A Skill is a specialized AI capability with its own system prompt,
    optional function-calling tools, and structured input/output schemas.

    The router LLM selects which skill to invoke based on the user's intent
    and the skill's `match` method.
    """

    name: str = ""
    description: str = ""
    version: str = "0.1.0"

    @abstractmethod
    def system_prompt(self, context: dict | None = None) -> str:
        """Return the system prompt that primes the LLM for this skill."""
        ...

    @abstractmethod
    def input_schema(self) -> dict:
        """JSON Schema describing the expected input fields."""
        ...

    def tools(self) -> list[dict]:
        """Optional function-calling tool definitions."""
        return []

    def match(self, user_intent: str) -> float:
        """Return a confidence score 0-1 for whether this skill matches the intent.
        Override in subclasses for keyword / semantic matching.
        """
        return 0.0

    async def execute(
        self, ai_service, user_input: dict, context: dict | None = None
    ) -> SkillResult:
        """Default execution: send system_prompt + user_input to the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": str(user_input)},
        ]
        response = await ai_service.chat(messages)
        return SkillResult(content=response)

    async def execute_streaming(
        self, ai_service, user_input: dict, context: dict | None = None
    ):
        """Override for streaming responses."""
        raise NotImplementedError
