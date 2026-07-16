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

class AnalyzeRequest(BaseModel):
    team1_id: int
    team2_id: int
    league_id: int
    season: int

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Invokes the Phase 1 graph: fetches form, head-to-head, injuries, and
    standings for the two teams, then returns a dummy synthesized report.
    Real LLM synthesis gets wired in during Phase 2.
    """
    initial_state = {
        "team1_id": req.team1_id,
        "team2_id": req.team2_id,
        "league_id": req.league_id,
        "season": req.season,
    }





