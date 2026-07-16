"""
Node functions for the match analysis graph.

Phase 3 scope: entry node `classify_query` fetches the fixture and
determines whether it's pre-match, live, or post-match, then the graph
routes (via edges.py) into one of three paths:

    pre_match  -> fetch_team_form -> fetch_head_to_head
              -> fetch_injuries -> fetch_standings -> synthesize_report
    post_match -> fetch_match_stats -> fetch_match_events -> synthesize_report
    live       -> live_placeholder (stub - full polling lands in Phase 4)
              -> synthesize_report

All paths converge on the same synthesize_report (LLM) node.
"""

from app.api_football.client import APIFootballClient
from app.graph.state import MatchAnalysisState
from app.llm.report_writer import synthesize_report_llm  # noqa: F401 - re-exported for build_graph

_client = APIFootballClient()

# API-Football fixture status short codes, grouped into our three categories.
# Reference: https://www.api-football.com/documentation-v3#tag/Fixtures
_PRE_MATCH_STATUSES = {"TBD", "NS"}
_LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "LIVE"}
_POST_MATCH_STATUSES = {"FT", "AET", "PEN", "PST", "CANC", "ABD", "AWD", "WO"}


async def classify_query(state: MatchAnalysisState) -> dict:
    """
    Entry node. Given a fixture_id, fetches the fixture from API-Football,
    extracts team/league/season, and classifies match status into one of
    "pre_match" / "live" / "post_match" for routing.
    """
    fixtures = await _client.get_fixture(state["fixture_id"])
    if not fixtures:
        raise ValueError(f"No fixture found for id {state['fixture_id']}")

    fixture_data = fixtures[0]
    status_short = fixture_data["fixture"]["status"]["short"]

    if status_short in _PRE_MATCH_STATUSES:
        category = "pre_match"
    elif status_short in _LIVE_STATUSES:
        category = "live"
    else:
        # Anything unrecognized falls back to post_match rather than
        # crashing the graph - safer default for a status code we haven't
        # explicitly mapped yet.
        category = "post_match"

    return {
        "team1_id": fixture_data["teams"]["home"]["id"],
        "team2_id": fixture_data["teams"]["away"]["id"],
        "league_id": fixture_data["league"]["id"],
        "season": fixture_data["league"]["season"],
        "match_status": status_short,
        "match_status_category": category,
    }


# ---------- pre-match path ----------

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


# ---------- post-match path ----------

async def fetch_match_stats(state: MatchAnalysisState) -> dict:
    stats = await _client.get_fixture_statistics(state["fixture_id"])
    return {"match_stats": stats}


async def fetch_match_events(state: MatchAnalysisState) -> dict:
    events = await _client.get_fixture_events(state["fixture_id"])
    return {"match_events": events}


# ---------- live path (stub - real polling/cycle lands in Phase 4) ----------

async def live_placeholder(state: MatchAnalysisState) -> dict:
    """
    Placeholder for the live path. Phase 4 will replace this with a node
    that polls fetch_fixture_events on an interval and loops via a
    conditional edge until the match ends.
    """
    events = await _client.get_fixture_events(state["fixture_id"])
    return {"match_events": events}