from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from src.models.base import BaseModelProvider
from src.config.settings import get_settings


class GeminiProvider(BaseModelProvider):
    """Routes Gemini calls through OpenRouter using the OpenAI-compatible API."""

    def __init__(self, model_override: str | None = None):
        self._settings = get_settings()
        self._model_name = model_override or self._settings.gemini_model

    def get_chat_model(
        self, temperature: float = 0.0, json_mode: bool = False,
    ) -> BaseChatModel:
        kwargs: dict = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return ChatOpenAI(
            model=self._model_name,
            temperature=temperature,
            api_key=self._settings.openrouter_api_key,
            base_url=self._settings.openrouter_base_url,
            model_kwargs=kwargs,
            request_timeout=60,
        )

    def get_model_name(self) -> str:
        return self._model_name
