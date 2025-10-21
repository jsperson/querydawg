"""
Abstract base classes for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    tokens_used: int
    cost_usd: float
    generation_time_ms: int
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    # Pricing per 1M tokens (input, output) - to be defined by subclasses
    PRICING: Dict[str, Dict[str, float]] = {}

    def __init__(self, api_key: str, model: str):
        """
        Initialize LLM provider

        Args:
            api_key: API key for the provider
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self._validate_model()

    def _validate_model(self):
        """Validate that the model is supported"""
        if self.model not in self.PRICING:
            raise ValueError(
                f"Model '{self.model}' not supported. "
                f"Available models: {list(self.PRICING.keys())}"
            )

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate completion from prompts

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with standardized fields
        """
        pass

    def get_cost_per_token(self) -> Dict[str, float]:
        """
        Get cost per token for the current model

        Returns:
            Dict with 'input' and 'output' costs per token
        """
        return self.PRICING[self.model]

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost in USD for token usage

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = self.get_cost_per_token()
        cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
        return cost
