"""
OpenAI LLM implementation for text-to-SQL and semantic layer generation.
"""

from typing import Optional
from openai import OpenAI
from .base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI API implementation."""

    # OpenAI pricing per 1M tokens (as of January 2025)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini)
        """
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        self.last_usage = {}

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using OpenAI API.

        Args:
            prompt: The user prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Store usage stats
        usage = response.usage
        self.last_usage = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

        # Calculate cost
        model_key = self.model
        if model_key not in self.PRICING:
            # Default to gpt-4o-mini pricing if model not found
            model_key = "gpt-4o-mini"

        pricing = self.PRICING[model_key]
        cost_usd = (
            (usage.prompt_tokens / 1_000_000) * pricing["input"] +
            (usage.completion_tokens / 1_000_000) * pricing["output"]
        )
        self.last_usage["cost_usd"] = cost_usd

        return response.choices[0].message.content

    def get_usage_stats(self) -> dict:
        """
        Get usage statistics from the last API call.

        Returns:
            Dictionary with usage statistics
        """
        return self.last_usage.copy()
