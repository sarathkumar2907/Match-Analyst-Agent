# ⚽ Match Analyst Agent

A LangGraph-based agentic pipeline, served over FastAPI, that generates
football match reports by autonomously gathering and synthesizing data
from the [API-Football](https://www.api-football.com/) API.

Given a fixture or matchup, the agent determines whether the match is
upcoming, live, or completed, then routes through a graph of specialized
nodes to fetch the right data — team form, head-to-head history, injuries,
live events, or post-match stats — before an LLM node synthesizes it into
a readable scouting report.

## Why this project

This started as a small learning project to explore **LangGraph**
(state graphs, conditional routing, parallel fan-out nodes, and cycles)
alongside **FastAPI** (async endpoints, background tasks, and SSE streaming),
using real sports data instead of toy examples.

## Status

🚧 **Work in progress / learning project — not production-ready.**

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | FastAPI skeleton + API-Football sanity check (`/health`, `/fixtures/today`) | ✅ Done |
| 1 | Linear pre-match graph (form, h2h, injuries, standings) + dummy synthesis | ✅ Done |
| 2 | Real LLM synthesis node (replaces dummy report) | ⏳ Next |
| 3 | Conditional routing: pre-match / live / post-match paths | ⏳ Planned |
| 4 | Live-match polling path (cycles in the graph) | ⏳ Planned |
| 5 | Streaming endpoint + in-memory caching | ⏳ Planned |
| 6 | Optional: Redis cache, checkpointing, deployment | ⏳ Stretch goal |

## Architecture

```
                        ┌─────────────────────┐
                        │      FastAPI         │
                        │  (API layer)          │
                        │                       │
                        │  POST /analyze        │
                        │  GET  /analyze/stream │  (Phase 5)
                        │  GET  /fixtures/today │
                        │  GET  /health         │
                        └──────────┬────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   LangGraph Runner    │
                        │  (compiled graph,     │
                        │   invoked per request)│
                        └──────────┬────────────┘
                                   │
        ┌──────────────────────────┼───────────────────────────┐
        ▼                          ▼                           ▼
 ┌───────────────┐        ┌───────────────────┐       ┌────────────────┐
 │ classify_query │        │  fetch_* nodes      │       │ synthesize_report│
 │ (routing node, │───────▶│  (tool nodes,        │──────▶│ (LLM node)       │
 │  Phase 3)      │        │   parallel fan-out)  │       └────────────────┘
 └───────────────┘        └──────────┬───────────┘
                                      ▼
                           ┌───────────────────┐
                           │  API-Football       │
                           │  client (httpx)     │
                           │  + cache layer       │
                           │  (Phase 5)           │
                           └───────────────────┘

Shared state object (TypedDict) flows through every node.
Cache: in-memory dict (Phase 5) -> Redis (Phase 6, optional).
LLM: OpenAI SDK called only in the synthesize_report node.
```

Currently implemented (Phases 0-1) is the **linear pre-match path only**:

```
START -> fetch_team_form -> fetch_head_to_head -> fetch_injuries
      -> fetch_standings -> synthesize_report (dummy) -> END
```

Conditional routing, the live-match cycle, and the real LLM node come in
later phases — see the table above.

## Tech stack

- **[LangGraph](https://langchain-ai.github.io/langgraph/)** — agent orchestration and state management
- **[FastAPI](https://fastapi.tiangolo.com/)** — API layer and (later) streaming responses
- **[API-Football](https://www.api-football.com/)** — match, team, and player data
- **OpenAI** — report synthesis (Phase 2+)

## Project structure

```
match-analyst-agent/
├── app/
│   ├── main.py                 # FastAPI app, route definitions
│   ├── config.py               # env vars / settings via pydantic-settings
│   ├── api_football/
│   │   ├── client.py           # async httpx wrapper around API-Football
│   │   └── cache.py            # in-memory cache w/ TTL (Phase 5, not yet added)
│   ├── graph/
│   │   ├── state.py            # shared MatchAnalysisState schema
│   │   ├── nodes.py            # all node functions
│   │   ├── edges.py            # conditional routing logic (Phase 3, not yet added)
│   │   └── build_graph.py      # assembles nodes + edges into a compiled graph
│   └── llm/
│       └── report_writer.py    # prompt + call for synthesize_report (Phase 2, not yet added)
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/sarathkumar2907/Match-Analyst-Agent.git
cd match-analyst-agent
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp .env.example .env
```

Then fill in `.env` with your real keys:

| Variable | Description |
|---|---|
| `API_FOOTBALL_KEY` | Your API-Football API key |
| `API_FOOTBALL_BASE_URL` | `https://v3.football.api-sports.io` (direct) or the RapidAPI host, depending on how you signed up |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Defaults to `gpt-4o-mini` |
| `APP_ENV` | `development` / `production` |
| `LOG_LEVEL` | e.g. `INFO`, `DEBUG` |
| `CACHE_TTL_SECONDS` | Reserved for Phase 5's cache layer; unused for now |
| `HOST` / `PORT` | Uvicorn bind settings |

**4. Run the app**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive
docs at `http://localhost:8000/docs`.

## API reference (current)

### `GET /health`

Basic liveness check.

```bash
curl http://localhost:8000/health
```
```json
{ "status": "ok" }
```

### `GET /fixtures/today`

Direct passthrough to API-Football — no LangGraph involved. Useful for
confirming your API key and base URL are correctly configured.

```bash
curl http://localhost:8000/fixtures/today
```

### `POST /analyze`

Runs the Phase 1 graph: fetches recent form, head-to-head history,
injuries, and standings for two teams, then returns a dummy synthesized
report (real LLM synthesis lands in Phase 2).

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
        "team1_id": 33,
        "team2_id": 40,
        "league_id": 39,
        "season": 2023
      }'
```

> **Note:** the team/league IDs above are illustrative. Confirm current
> IDs via API-Football's `/teams?search=` and `/leagues?search=` endpoints
> before relying on them.

## Roadmap / what's next

See the phase table above. The immediate next step (Phase 2) is replacing
`synthesize_report_dummy` in `app/graph/nodes.py` with a real call to
OpenAI that turns the gathered state into a readable scouting report.

## Rate limits

API-Football's free tier has a fairly strict daily request cap. Until the
Phase 5 cache lands, every `/analyze` call hits the live API on every
fetch node with no caching — keep an eye on your quota while testing
repeatedly.

## License


