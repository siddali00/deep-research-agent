from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    target: str
    iterations: int
    total_facts: int
    avg_confidence: float
    total_risks: int
    critical_risks: int
    high_risks: int
    connections: int
    queries_executed: int


class RiskFlagResponse(BaseModel):
    risk_category: str
    severity: str
    description: str
    supporting_facts: list[int] = []
    recommendations: list[str] = []


class GraphDataResponse(BaseModel):
    nodes: list[dict]
    relationships: list[dict]
