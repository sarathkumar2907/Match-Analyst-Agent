"""
Node functions for the match analysis graph.

Phase 1 scope: linear pre-match pipeline, no LLM yet.
    fetch_team_form -> fetch_head_to_head -> fetch_injuries -> fetch_standings -> synthesize_report (dummy)

Each node takes the current state dict and returns a partial dict of
updates - this is the standard LangGraph node signature. LangGraph merges
the returned dict into the running state for you.
"""

from app.api_football.client import APIFootballClient
from app.graph.state import MatchAnalysisState

_client = APIFootballClient()


async def fetch_team_form(state: MatchAnalysisState) -> dict:
    team1_form = await _client.get_team_last_fixtures(state["team1_id"], last=5)
    team2_form = await _client.get_team_last_fixtures(state["team2_id"], last=5)
    return {"team1_form": team1_form, "team2_form": team2_form}


async def fetch_head_to_head(state: MatchAnalysisState) -> dict:
    h2h = await _client.get_head_to_head(state["team1_id"], state["team2_id"], last=5)
    return {"head_to_head": h2h}


async def fetch_injuries(state: MatchAnalysisState) -> dict:
    team1_injuries = await _client.get_injuries(state["team1_id"], state["season"])
    team2_injuries = await _client.get_injuries(state["team2_id"], state["season"])
    return {"team1_injuries": team1_injuries, "team2_injuries": team2_injuries}


async def fetch_standings(state: MatchAnalysisState) -> dict:
    standings = await _client.get_standings(state["league_id"], state["season"])
    return {"standings": standings}


async def synthesize_report_dummy(state: MatchAnalysisState) -> dict:
    """
    Placeholder synthesis node for Phase 1. Just dumps a readable summary
    of what was gathered, so we can prove the graph runs end-to-end before
    wiring in a real LLM call in Phase 2.
    """
    report_lines = [
        "=== Match Analysis (Phase 1 - dummy synthesis) ===",
        f"Team 1 form: {len(state.get('team1_form', []))} recent fixtures fetched",
        f"Team 2 form: {len(state.get('team2_form', []))} recent fixtures fetched",
        f"Head-to-head: {len(state.get('head_to_head', []))} past meetings fetched",
        f"Team 1 injuries: {len(state.get('team1_injuries', []))} reported",
        f"Team 2 injuries: {len(state.get('team2_injuries', []))} reported",
        f"Standings entries: {len(state.get('standings', []))}",
    ]
    return {"report": "\n".join(report_lines)}
