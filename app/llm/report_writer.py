"""
Builds a scouting/match report from whatever the graph gathered in state,
using OpenAI's chat completions API.

Handles pre-match, post-match, and (stub) live state shapes gracefully -
it just describes whatever fields are present, since Phase 3 routes
different amounts of data into state depending on match status.
"""

import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.graph.state import MatchAnalysisState

_settings = get_settings()
_client = AsyncOpenAI(api_key=_settings.openai_api_key)

SYSTEM_PROMPT = """You are a football (soccer) match analyst. You will be given
raw JSON data gathered from the API-Football API about a specific fixture -
this may include recent form, head-to-head history, injuries, standings,
match statistics, or match events, depending on whether the match is
upcoming, live, or finished.

Write a concise, readable report (roughly 150-250 words) aimed at a fan
who wants a quick, informed summary. Only reference facts present in the
data - do not invent scores, players, or events that aren't in the data.
If some data is missing, just work with what's available rather than
mentioning the gap."""


def _build_user_prompt(state: MatchAnalysisState) -> str:
    # Only include fields that were actually populated, so the prompt
    # stays relevant to whichever path (pre/live/post) the graph took.
    relevant_keys = [
        "match_status",
        "team1_form",
        "team2_form",
        "head_to_head",
        "team1_injuries",
        "team2_injuries",
        "standings",
        "match_stats",
        "match_events",
    ]
    data = {k: state[k] for k in relevant_keys if k in state}
    return f"Match data:\n{json.dumps(data, default=str)}"


async def synthesize_report_llm(state: MatchAnalysisState) -> dict:
    user_prompt = _build_user_prompt(state)

    response = await _client.chat.completions.create(
        model=_settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    report = response.choices[0].message.content
    return {"report": report}