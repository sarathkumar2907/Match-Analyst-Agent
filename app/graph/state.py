"""
Shared state object that flows through every node in the graph.

Phase 1 keeps this deliberately flat and pre-match only. Later phases
(conditional routing, live path) will add fields like `match_status`,
`live_events`, `match_stats` - add them incrementally rather than
front-loading everything now.
"""

from typing import Any, TypedDict


class MatchAnalysisState(TypedDict, total=False):
    # ---- inputs ----
    team1_id: int
    team2_id: int
    league_id: int
    season: int

    # ---- gathered data (populated by fetch_* nodes) ----
    team1_form: list[dict[str, Any]]
    team2_form: list[dict[str, Any]]
    head_to_head: list[dict[str, Any]]
    team1_injuries: list[dict[str, Any]]
    team2_injuries: list[dict[str, Any]]
    standings: list[dict[str, Any]]

    # ---- output ----
    report: str
