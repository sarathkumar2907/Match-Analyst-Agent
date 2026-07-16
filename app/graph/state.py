"""
Shared state object that flows through every node in the graph.

Phase 3 adds `fixture_id` and `match_status_category` (the routing key)
plus post-match fields (`match_stats`, `match_events`). The live path
fields are stubbed for now - full live polling support lands in Phase 4.
"""

from typing import Any, TypedDict


class MatchAnalysisState(TypedDict, total=False):
    # ---- inputs ----
    fixture_id: int
    team1_id: int
    team2_id: int
    league_id: int
    season: int

    # ---- routing (set by classify_query, Phase 3) ----
    match_status: str            # raw API-Football status short code, e.g. "NS", "1H", "FT"
    match_status_category: str   # normalized to "pre_match" / "live" / "post_match"

    # ---- pre-match data ----
    team1_form: list[dict[str, Any]]
    team2_form: list[dict[str, Any]]
    head_to_head: list[dict[str, Any]]
    team1_injuries: list[dict[str, Any]]
    team2_injuries: list[dict[str, Any]]
    standings: list[dict[str, Any]]

    # ---- post-match data ----
    match_stats: list[dict[str, Any]]
    match_events: list[dict[str, Any]]

    # ---- output ----
    report: str