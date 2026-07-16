"""
Assembles the Phase 1 graph: a linear pipeline, no conditional routing yet.

    START -> fetch_team_form -> fetch_head_to_head -> fetch_injuries
          -> fetch_standings -> synthesize_report -> END

Conditional routing (pre-match / live / post-match) gets added in Phase 3
by swapping the plain `add_edge` calls for `add_conditional_edges` from a
new `classify_query` entry node - deliberately not doing that yet so the
graph mechanics are easy to reason about first.
"""

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    fetch_head_to_head,
    fetch_injuries,
    fetch_standings,
    fetch_team_form,
    synthesize_report_dummy,
)
from app.graph.state import MatchAnalysisState


def build_graph():
    graph = StateGraph(MatchAnalysisState)

    graph.add_node("fetch_team_form", fetch_team_form)
    graph.add_node("fetch_head_to_head", fetch_head_to_head)
    graph.add_node("fetch_injuries", fetch_injuries)
    graph.add_node("fetch_standings", fetch_standings)
    graph.add_node("synthesize_report", synthesize_report_dummy)

    graph.add_edge(START, "fetch_team_form")
    graph.add_edge("fetch_team_form", "fetch_head_to_head")
    graph.add_edge("fetch_head_to_head", "fetch_injuries")
    graph.add_edge("fetch_injuries", "fetch_standings")
    graph.add_edge("fetch_standings", "synthesize_report")
    graph.add_edge("synthesize_report", END)

    return graph.compile()


# Compiled once at import time; reused across requests.
match_analysis_graph = build_graph()
