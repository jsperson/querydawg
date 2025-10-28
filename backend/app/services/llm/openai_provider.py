"""
OpenAI API provider implementation
"""
import time
from typing import Optional
from openai import OpenAI
from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI API provider - supports all OpenAI models"""

    # Pricing per 1M tokens (as of January 2025)
    PRICING = {
        # GPT-4o series (latest, multimodal)
        "gpt-4o": {
            "input": 2.50 / 1_000_000,
            "output": 10.00 / 1_000_000
        },
        "gpt-4o-mini": {
            "input": 0.150 / 1_000_000,
            "output": 0.600 / 1_000_000
        },

        # GPT-4 Turbo
        "gpt-4-turbo": {
            "input": 10.00 / 1_000_000,
            "output": 30.00 / 1_000_000
        },
        "gpt-4-turbo-preview": {
            "input": 10.00 / 1_000_000,
            "output": 30.00 / 1_000_000
        },

        # GPT-4 (original)
        "gpt-4": {
            "input": 30.00 / 1_000_000,
            "output": 60.00 / 1_000_000
        },

        # GPT-3.5 Turbo
        "gpt-3.5-turbo": {
            "input": 0.50 / 1_000_000,
            "output": 1.50 / 1_000_000
        },

        # o1 series (reasoning models)
        "o1": {
            "input": 15.00 / 1_000_000,
            "output": 60.00 / 1_000_000
        },
        "o1-mini": {
            "input": 3.00 / 1_000_000,
            "output": 12.00 / 1_000_000
        },
    }

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4o-mini')
        """
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate completion using OpenAI API

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate (None = model default)

        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Call OpenAI API
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**kwargs)

        # Calculate timing and cost
        generation_time_ms = int((time.time() - start_time) * 1000)
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        cost_usd = self.calculate_cost(prompt_tokens, completion_tokens)

        # Extract content safely
        content = response.choices[0].message.content
        if content is None:
            raise ValueError(f"OpenAI returned None content. Response: {response}")

        return LLMResponse(
            content=content.strip(),
            tokens_used=total_tokens,
            cost_usd=cost_usd,
            generation_time_ms=generation_time_ms,
            model=self.model,
            provider="openai",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
