from pydantic import BaseModel, Field
from datetime import datetime


class PersonNode(BaseModel):
    name: str
    role: str | None = None
    organization: str | None = None
    description: str | None = None
    source_url: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationNode(BaseModel):
    name: str
    org_type: str | None = None  # company, fund, non-profit, government
    industry: str | None = None
    location: str | None = None
    description: str | None = None
    source_url: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class EventNode(BaseModel):
    name: str
    event_type: str | None = None  # lawsuit, filing, transaction, appointment
    date: str | None = None
    description: str | None = None
    source_url: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class LocationNode(BaseModel):
    name: str
    location_type: str | None = None  # city, state, country
    description: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentNode(BaseModel):
    title: str
    url: str
    doc_type: str | None = None  # news, filing, report
    published_date: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
