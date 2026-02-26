from fastapi import APIRouter

from src.api.schemas.reports import GraphDataResponse
from src.api.controllers import graph as ctrl

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/{research_id}", response_model=GraphDataResponse)
def get_identity_graph(research_id: str):
    data = ctrl.get_graph_data(research_id)
    return GraphDataResponse(
        nodes=data.get("nodes", []),
        relationships=data.get("relationships", []),
    )
