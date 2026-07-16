"""
Thin async wrapper around the API-Football v3 REST API.

Only the endpoints this project needs are covered. Each method returns
the raw `response` list from the API-Football payload (i.e. `data["response"]`),
already unwrapped, so callers don't need to know the envelope shape.

Docs: https://www.api-football.com/documentation-v3
"""

from typing import Any

import httpx

from app.config import get_settings


class APIFootballError(Exception):
    """Raised when API-Football returns a non-2xx response or an API-level error."""


class APIFootballClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.api_football_base_url
        self._headers = {"x-apisports-key": settings.api_football_key}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=15) as client:
            resp = await client.get(path, params=params or {})

        if resp.status_code != 200:
            raise APIFootballError(f"{path} returned {resp.status_code}: {resp.text}")

        payload = resp.json()

        # API-Football embeds errors in the JSON body even on 200 responses.
        if payload.get("errors"):
            raise APIFootballError(f"{path} returned API errors: {payload['errors']}")

        return payload.get("response", [])

    async def get_fixtures_by_date(self, date: str) -> list[Any]:
        """date format: YYYY-MM-DD"""
        return await self._get("/fixtures", {"date": date})

    async def get_fixture(self, fixture_id: int) -> list[Any]:
        return await self._get("/fixtures", {"id": fixture_id})

    async def get_team_last_fixtures(self, team_id: int, last: int = 5) -> list[Any]:
        """Recent form: last N finished fixtures for a team."""
        return await self._get("/fixtures", {"team": team_id, "last": last})

    async def get_head_to_head(self, team1_id: int, team2_id: int, last: int = 5) -> list[Any]:
        return await self._get("/fixtures/headtohead", {"h2h": f"{team1_id}-{team2_id}", "last": last})

    async def get_injuries(self, team_id: int, season: int) -> list[Any]:
        return await self._get("/injuries", {"team": team_id, "season": season})

    async def get_standings(self, league_id: int, season: int) -> list[Any]:
        return await self._get("/standings", {"league": league_id, "season": season})

    async def get_fixture_events(self, fixture_id: int) -> list[Any]:
        return await self._get("/fixtures/events", {"fixture": fixture_id})

    async def get_fixture_statistics(self, fixture_id: int) -> list[Any]:
        return await self._get("/fixtures/statistics", {"fixture": fixture_id})
