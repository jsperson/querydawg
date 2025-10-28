"""
LLM configuration for task-based model selection
"""
import os
from typing import Dict, Any
from .base import LLMProvider
from .openai_provider import OpenAIProvider


class LLMConfig:
    """Configuration for which models to use for different tasks"""

    # Task definitions with default models
    # Can be overridden via environment variables
    TASKS = {
        "baseline_sql": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 1000,
            "description": "Generate SQL from schema only (baseline)"
        },
        "enhanced_sql": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 1000,
            "description": "Generate SQL with RAG and examples (enhanced)"
        },
        "sql_explanation": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 500,
            "description": "Explain generated SQL in natural language"
        },
        "error_correction": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.0,
            "max_tokens": 1000,
            "description": "Fix SQL errors and syntax issues"
        },
        "schema_summary": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.0,
            "max_tokens": 500,
            "description": "Summarize database schema"
        },
        "semantic_layer": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.0,
            "max_tokens": 4000,
            "description": "Generate semantic layer documentation for databases"
        }
    }

    @classmethod
    def get_task_config(cls, task: str) -> Dict[str, Any]:
        """
        Get configuration for a specific task

        Args:
            task: Task name (e.g., 'baseline_sql')

        Returns:
            Configuration dictionary with provider, model, temperature, etc.

        Raises:
            ValueError: If task is not defined
        """
        if task not in cls.TASKS:
            raise ValueError(
                f"Unknown task: {task}. "
                f"Available tasks: {list(cls.TASKS.keys())}"
            )

        config = cls.TASKS[task].copy()

        # Allow environment variable overrides
        # e.g., BASELINE_SQL_PROVIDER=openai, BASELINE_SQL_MODEL=gpt-4o
        env_prefix = task.upper()

        provider_env = f"{env_prefix}_PROVIDER"
        if provider_env in os.environ:
            config["provider"] = os.getenv(provider_env)

        model_env = f"{env_prefix}_MODEL"
        if model_env in os.environ:
            config["model"] = os.getenv(model_env)

        return config

    @classmethod
    def get_provider_for_task(cls, task: str) -> LLMProvider:
        """
        Get configured LLM provider instance for a specific task

        Args:
            task: Task name (e.g., 'baseline_sql')

        Returns:
            LLMProvider instance configured for the task

        Raises:
            ValueError: If task is unknown or provider is unsupported
        """
        config = cls.get_task_config(task)

        provider = config["provider"]
        model = config["model"]

        # Get API key for provider
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            return OpenAIProvider(api_key=api_key, model=model)

        # Future providers can be added here:
        # elif provider == "together":
        #     api_key = os.getenv("TOGETHER_API_KEY")
        #     return TogetherProvider(api_key=api_key, model=model)
        # elif provider == "groq":
        #     api_key = os.getenv("GROQ_API_KEY")
        #     return GroqProvider(api_key=api_key, model=model)

        raise ValueError(f"Unsupported provider: {provider}")

    @classmethod
    def list_tasks(cls) -> Dict[str, str]:
        """
        List all available tasks with descriptions

        Returns:
            Dictionary mapping task names to descriptions
        """
        return {
            task: config["description"]
            for task, config in cls.TASKS.items()
        }
