from langchain_core.language_models import BaseChatModel

from src.config.models import ModelProvider, TaskType, TASK_MODEL_MAP, FALLBACK_MODEL_MAP
from src.models.openai_model import OpenAIProvider
from src.models.gemini import GeminiProvider
from src.models.base import BaseModelProvider


class ModelRouter:
    """Routes task types to the appropriate AI model provider."""

    def __init__(self):
        self._providers: dict[ModelProvider, BaseModelProvider] = {
            ModelProvider.OPENAI: OpenAIProvider(),
            ModelProvider.GEMINI: GeminiProvider(),
        }
        self._cache: dict[tuple, BaseChatModel] = {}

    def get_model(
        self,
        task: TaskType,
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> BaseChatModel:
        provider_key = TASK_MODEL_MAP[task]
        return self._get_cached(provider_key, temperature, json_mode)

    def get_fallback_model(
        self,
        task: TaskType,
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> BaseChatModel:
        """Return the fallback provider's model for a given task."""
        primary = TASK_MODEL_MAP[task]
        fallback = FALLBACK_MODEL_MAP[primary]
        return self._get_cached(fallback, temperature, json_mode)

    def _get_cached(
        self, provider: ModelProvider, temperature: float, json_mode: bool,
    ) -> BaseChatModel:
        key = (provider, temperature, json_mode)
        if key not in self._cache:
            self._cache[key] = self._providers[provider].get_chat_model(
                temperature=temperature, json_mode=json_mode,
            )
        return self._cache[key]

    def get_provider(self, task: TaskType) -> BaseModelProvider:
        provider_key = TASK_MODEL_MAP[task]
        return self._providers[provider_key]
