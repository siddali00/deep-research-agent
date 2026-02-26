from langgraph.graph import StateGraph, END

from src.graphs.state import ResearchState
from src.graphs.nodes.planner import planner_node
from src.graphs.nodes.searcher import searcher_node
from src.graphs.nodes.extractor import extractor_node
from src.graphs.nodes.analyzer import analyzer_node
from src.graphs.nodes.scorer import scorer_node
from src.graphs.nodes.validator import validator_node
from src.graphs.nodes.reporter import reporter_node
from src.graphs.edges.routing import route_after_validation


def build_research_graph() -> StateGraph:
    """Construct and compile the research agent state graph.

    Flow:
        planner -> searcher -> extractor -> [analyzer, scorer] (parallel)
            -> validator (fan-in, sufficiency check)
            -> (conditional) -> planner  (loop for more research)
            -> (conditional) -> reporter -> END
    """
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("searcher", searcher_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("scorer", scorer_node)
    graph.add_node("validator", validator_node)
    graph.add_node("reporter", reporter_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "searcher")
    graph.add_edge("searcher", "extractor")

    # Fan-out: extractor feeds both analyzer and scorer in parallel
    graph.add_edge("extractor", "analyzer")
    graph.add_edge("extractor", "scorer")

    # Fan-in: validator waits for both analyzer and scorer to complete
    graph.add_edge("analyzer", "validator")
    graph.add_edge("scorer", "validator")

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "planner": "planner",
            "reporter": "reporter",
        },
    )

    graph.add_edge("reporter", END)

    return graph.compile()
