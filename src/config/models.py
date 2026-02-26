from enum import Enum


class ModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class TaskType(str, Enum):
    PLANNING = "planning"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    REPORTING = "reporting"


TASK_MODEL_MAP: dict[TaskType, ModelProvider] = {
    TaskType.PLANNING: ModelProvider.OPENAI,
    TaskType.EXTRACTION: ModelProvider.OPENAI,
    TaskType.ANALYSIS: ModelProvider.OPENAI,
    TaskType.VALIDATION: ModelProvider.OPENAI,
    TaskType.REPORTING: ModelProvider.GEMINI,
}

FALLBACK_MODEL_MAP: dict[ModelProvider, ModelProvider] = {
    ModelProvider.OPENAI: ModelProvider.GEMINI,
    ModelProvider.GEMINI: ModelProvider.OPENAI,
}
