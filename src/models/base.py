from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel


class BaseModelProvider(ABC):
    @abstractmethod
    def get_chat_model(
        self, temperature: float = 0.0, json_mode: bool = False,
    ) -> BaseChatModel:
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        ...
