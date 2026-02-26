from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

from neo4j import GraphDatabase, Driver, Session

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Singleton wrapper around the Neo4j driver."""

    _instance: Neo4jClient | None = None
    _driver: Driver | None = None

    def __new__(cls) -> Neo4jClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> None:
        if self._driver is not None:
            return
        settings = get_settings()
        uri = settings.neo4j_uri

        # neo4j+ssc:// accepts self-signed certs (avoids SSL verify errors on Windows)
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "neo4j+ssc://", 1)
        elif uri.startswith("bolt+s://"):
            uri = uri.replace("bolt+s://", "bolt+ssc://", 1)

        self._driver = GraphDatabase.driver(
            uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self._driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", uri)

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if self._driver is None:
            self.connect()
        settings = get_settings()
        with self._driver.session(database=settings.neo4j_database) as session:
            yield session

    def run_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict]:
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def clear_database(self) -> None:
        """Remove all nodes and relationships (use with caution)."""
        self.run_query("MATCH (n) DETACH DELETE n")
        logger.warning("Neo4j database cleared")
