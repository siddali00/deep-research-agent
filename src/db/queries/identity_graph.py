from __future__ import annotations

import logging
import re
from typing import Any

from src.db.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class IdentityGraphQueries:
    """Cypher query builder for the identity graph."""

    def __init__(self):
        self._client = Neo4jClient()

    def create_person(self, name: str, properties: dict[str, Any] | None = None) -> None:
        props = properties or {}
        self._client.run_query(
            "MERGE (p:Person {name: $name}) SET p += $props",
            {"name": name, "props": props},
        )

    def create_organization(self, name: str, properties: dict[str, Any] | None = None) -> None:
        props = properties or {}
        self._client.run_query(
            "MERGE (o:Organization {name: $name}) SET o += $props",
            {"name": name, "props": props},
        )

    def create_event(self, name: str, properties: dict[str, Any] | None = None) -> None:
        props = properties or {}
        self._client.run_query(
            "MERGE (e:Event {name: $name}) SET e += $props",
            {"name": name, "props": props},
        )

    def create_location(self, name: str, properties: dict[str, Any] | None = None) -> None:
        props = properties or {}
        self._client.run_query(
            "MERGE (l:Location {name: $name}) SET l += $props",
            {"name": name, "props": props},
        )

    def create_document(self, title: str, url: str, properties: dict[str, Any] | None = None) -> None:
        props = properties or {}
        props["url"] = url
        self._client.run_query(
            "MERGE (d:Document {title: $title}) SET d += $props",
            {"title": title, "props": props},
        )

    def create_relationship(
        self,
        source_label: str,
        source_name: str,
        target_label: str,
        target_name: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        props = properties or {}
        query = (
            f"MATCH (a:{source_label} {{name: $source_name}}) "
            f"MATCH (b:{target_label} {{name: $target_name}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
        )
        self._client.run_query(
            query,
            {"source_name": source_name, "target_name": target_name, "props": props},
        )

    def get_full_graph(self) -> dict:
        nodes = self._client.run_query(
            "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props"
        )
        rels = self._client.run_query(
            "MATCH (a)-[r]->(b) RETURN id(a) AS source, id(b) AS target, "
            "type(r) AS type, properties(r) AS props"
        )
        return {"nodes": nodes, "relationships": rels}

    def get_person_graph(self, name: str) -> dict:
        nodes_and_rels = self._client.run_query(
            "MATCH (p:Person {name: $name})-[r]-(connected) "
            "RETURN p, r, connected",
            {"name": name},
        )
        return nodes_and_rels

    def build_from_research(self, target_name: str, facts: list[dict], connections: list[dict]) -> None:
        """Build the full identity graph from research results using batched queries."""
        logger.info("Building identity graph for %s", target_name)

        persons: list[dict] = [{"name": target_name, "props": {"role": "research_target"}}]
        organizations: list[dict] = []
        documents: list[dict] = []
        entity_types: dict[str, str] = {}

        for fact in facts:
            for entity in fact.get("entities", []):
                if entity.lower() == target_name.lower() or entity in entity_types:
                    continue
                category = fact.get("category", "")
                if category in ("professional", "financial"):
                    organizations.append({"name": entity, "props": {}})
                    entity_types[entity] = "Organization"
                else:
                    persons.append({"name": entity, "props": {}})
                    entity_types[entity] = "Person"

            if fact.get("source_url") and fact.get("source_title"):
                documents.append({
                    "title": fact["source_title"],
                    "props": {"url": fact["source_url"], "confidence": fact.get("confidence", 0.5)},
                })

        with self._client.session() as session:
            if persons:
                session.run(
                    "UNWIND $batch AS item MERGE (p:Person {name: item.name}) SET p += item.props",
                    {"batch": persons},
                )
            if organizations:
                session.run(
                    "UNWIND $batch AS item MERGE (o:Organization {name: item.name}) SET o += item.props",
                    {"batch": organizations},
                )
            if documents:
                session.run(
                    "UNWIND $batch AS item MERGE (d:Document {title: item.title}) SET d += item.props",
                    {"batch": documents},
                )

            for conn in connections:
                source = conn.get("source_entity", "")
                target = conn.get("target_entity", "")
                rel_type = _sanitize_rel_type(conn.get("relationship", "ASSOCIATED_WITH"))
                source_label = entity_types.get(source, "Person")
                target_label = entity_types.get(target, "Person")

                try:
                    session.run(
                        f"MATCH (a:{source_label} {{name: $source_name}}) "
                        f"MATCH (b:{target_label} {{name: $target_name}}) "
                        f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props",
                        {
                            "source_name": source,
                            "target_name": target,
                            "props": {
                                "description": conn.get("description", ""),
                                "confidence": conn.get("confidence", 0.5),
                            },
                        },
                    )
                except Exception as e:
                    logger.warning("Failed to create relationship %s->%s: %s", source, target, e)

        logger.info("Identity graph built: processed %d facts, %d connections", len(facts), len(connections))


def _sanitize_rel_type(raw: str) -> str:
    """Sanitize a relationship type for Neo4j Cypher.

    Neo4j only allows letters, digits, and underscores in relationship types.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", raw.upper())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_") or "ASSOCIATED_WITH"
