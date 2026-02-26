import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.config.settings import get_settings


def setup_logging() -> None:
    """Configure structured logging. LangSmith tracing is handled automatically
    by the SDK via LANGSMITH_* env vars loaded from .env."""
    load_dotenv()
    settings = get_settings()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    root_logger.addHandler(console_handler)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_filename = f"research_agent_{timestamp}.log"

    file_handler = logging.FileHandler(log_dir / log_filename, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    if settings.langsmith_tracing:
        logging.info(
            "LangSmith tracing enabled for project: %s", settings.langsmith_project
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
