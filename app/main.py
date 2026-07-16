from fastapi import FastAPI,HTTPException
from datetime import date
from pydantic import BaseModel
from app.api_football.client import APIFootballClient, APIFootballError
from app.graph.build_graph import match_analysis_graph

app = FastAPI(title="MatchAnalystAgent", 
              description="A FastAPI application for Match Analyst Agent", 
              version="1.0.0")

_client = APIFootballClient()

@app.get("/health", tags=["Health Check"])
async def health():
    return {"status": "OK", "message": "Welcome to MatchAnalystAgent!"}

@app.get("/fixtures/today", tags=["Fixtures"])
async def fixtures_today():
    """
    Direct passthrough to API-Football, no LangGraph involved.
    Exists purely to confirm your API key/base URL/auth header are correct
    before any graph code runs.
    """
    today_str = date.today().isoformat()
    try:
        fixtures = await _client.get_fixtures_by_date(today_str)
    except APIFootballError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"date": today_str, "count": len(fixtures), "fixtures": fixtures}

# ---------- Phase 2/3: full graph, routed by match status ----------

class AnalyzeRequest(BaseModel):
    fixture_id: int


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Invokes the graph for a given fixture_id. The entry node
    (classify_query) fetches the fixture, derives team/league/season,
    and classifies it as pre_match / live / post_match - the graph then
    routes to the matching path and returns an LLM-synthesized report.
    """
    initial_state = {"fixture_id": req.fixture_id}

    try:
        result = await match_analysis_graph.ainvoke(initial_state)
    except APIFootballError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        # e.g. classify_query couldn't find the fixture
        raise HTTPException(status_code=404, detail=str(e))

    return result



