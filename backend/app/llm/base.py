"""
Base LLM interface for text-to-SQL and semantic layer generation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: str):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the LLM provider
            model: Model identifier (e.g., 'gpt-4o-mini', 'claude-3-sonnet')
        """
        self.api_key = api_key
        self.model = model
        self.provider = self.__class__.__name__.replace("LLM", "").lower()

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The user prompt
            system_message: Optional system message/instruction
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_usage_stats(self) -> dict:
        """
        Get usage statistics from the last API call.

        Returns:
            Dictionary with keys: prompt_tokens, completion_tokens, total_tokens, cost_usd
        """
        pass
