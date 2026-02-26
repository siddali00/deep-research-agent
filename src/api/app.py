from fastapi import FastAPI

from src.api.routers import research, graph, reports
from src.utils.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Deep Research AI Agent",
        description="Autonomous research agent for intelligence gathering and risk assessment",
        version="0.1.0",
    )

    app.include_router(research.router)
    app.include_router(graph.router)
    app.include_router(reports.router)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
