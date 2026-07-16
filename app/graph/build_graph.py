"""
Assembles the Phase 3 graph: an entry `classify_query` node routes into
one of three paths based on match status, and all paths converge on the
real LLM `synthesize_report` node.

    START -> classify_query
                 |-- pre_match  --> fetch_team_form -> fetch_head_to_head
                 |                  -> fetch_injuries -> fetch_standings --+
                 |-- live       --> live_placeholder ---------------------+
                 |-- post_match --> fetch_match_stats -> fetch_match_events+
                                                                           v
                                                              synthesize_report -> END

Phase 4 will replace `live_placeholder` with a real polling node that
cycles (via a conditional edge back to itself) until the match ends.
"""

from langgraph.graph import END, START, StateGraph

from app.graph.edges import route_by_match_status
from app.graph.nodes import (
    classify_query,
    fetch_head_to_head,
    fetch_injuries,
    fetch_match_events,
    fetch_match_stats,
    fetch_standings,
    fetch_team_form,
    live_placeholder,
)
from app.graph.state import MatchAnalysisState
from app.llm.report_writer import synthesize_report_llm


def build_graph():
    graph = StateGraph(MatchAnalysisState)

    # ---- nodes ----
    graph.add_node("classify_query", classify_query)

    graph.add_node("fetch_team_form", fetch_team_form)
    graph.add_node("fetch_head_to_head", fetch_head_to_head)
    graph.add_node("fetch_injuries", fetch_injuries)
    graph.add_node("fetch_standings", fetch_standings)

    graph.add_node("fetch_match_stats", fetch_match_stats)
    graph.add_node("fetch_match_events", fetch_match_events)

    graph.add_node("live_placeholder", live_placeholder)

    graph.add_node("synthesize_report", synthesize_report_llm)

    # ---- entry ----
    graph.add_edge(START, "classify_query")

    # ---- conditional routing out of classify_query ----
    graph.add_conditional_edges(
        "classify_query",
        route_by_match_status,
        {
            "pre_match": "fetch_team_form",
            "live": "live_placeholder",
            "post_match": "fetch_match_stats",
        },
    )

    # ---- pre-match path (linear) ----
    graph.add_edge("fetch_team_form", "fetch_head_to_head")
    graph.add_edge("fetch_head_to_head", "fetch_injuries")
    graph.add_edge("fetch_injuries", "fetch_standings")
    graph.add_edge("fetch_standings", "synthesize_report")

    # ---- post-match path (linear) ----
    graph.add_edge("fetch_match_stats", "fetch_match_events")
    graph.add_edge("fetch_match_events", "synthesize_report")

    # ---- live path (stub for now) ----
    graph.add_edge("live_placeholder", "synthesize_report")

    # ---- convergence ----
    graph.add_edge("synthesize_report", END)

    return graph.compile()


# Compiled once at import time; reused across requests.
match_analysis_graph = build_graph()