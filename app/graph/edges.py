"""
Conditional routing logic, used by build_graph.py's `add_conditional_edges`.

Kept as a plain function returning a string key - LangGraph maps that key
to a destination node name via the `path_map` dict passed at the call site.
"""

from app.graph.state import MatchAnalysisState


def route_by_match_status(state: MatchAnalysisState) -> str:
    """
    Reads `match_status_category` (set by classify_query) and returns the
    routing key. Falls back to "pre_match" if somehow unset, rather than
    raising - keeps the graph resilient to an unexpected state shape.
    """
    return state.get("match_status_category", "pre_match")