from pydantic import BaseModel, Field
from datetime import datetime


class BaseRelationship(BaseModel):
    source_url: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    description: str | None = None


class WorksAt(BaseRelationship):
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Founded(BaseRelationship):
    date: str | None = None


class InvestedIn(BaseRelationship):
    amount: str | None = None
    date: str | None = None


class AssociatedWith(BaseRelationship):
    association_type: str | None = None


class BoardMemberOf(BaseRelationship):
    start_date: str | None = None
    end_date: str | None = None


class MentionedIn(BaseRelationship):
    context: str | None = None


class LocatedIn(BaseRelationship):
    pass


RELATIONSHIP_TYPES = [
    "WORKS_AT",
    "FOUNDED",
    "INVESTED_IN",
    "ASSOCIATED_WITH",
    "BOARD_MEMBER_OF",
    "MENTIONED_IN",
    "LOCATED_IN",
]
