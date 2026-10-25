"""The API. Run:  uvicorn backend.main:app --reload   then open http://localhost:8000/docs
That /docs page is a free test screen for every endpoint."""
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import llm, matcher, store
from .models import Match, Opportunity, StudentProfile

app = FastAPI(title="OppFinder API", version="0.1.0",
              description="Match OAU students to scholarships, internships, jobs and learning opportunities.")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/opportunities", response_model=List[Opportunity])
def list_opportunities(include_examples: bool = False):
    items = store.load_opportunities()
    return items if include_examples else [o for o in items if not o.is_example]


class MatchRequest(BaseModel):
    profile: StudentProfile
    explain: bool = True          # set False for instant results without the model
    limit: int = 5                # only the top N get a model explanation (keeps it fast)
    include_examples: bool = False


@app.post("/match", response_model=List[Match])
def match(req: MatchRequest):
    results = matcher.match(req.profile, store.load_opportunities(),
                            include_examples=req.include_examples)
    if req.explain:
        for m in results[: req.limit]:
            try:
                m.explanation = llm.explain_match(req.profile, m.opportunity)
            except llm.LLMUnavailable:
                m.explanation = ""   # the screen still shows the rule-based reasons
    return results


class ExtractRequest(BaseModel):
    raw_text: str
    source_link: str = ""         # official page the text came from
    new_id: str


@app.post("/extract", response_model=Opportunity)
def extract(req: ExtractRequest):
    """Draft only. A human must check it, then call POST /opportunities to save."""
    try:
        return llm.extract_opportunity(req.raw_text, req.new_id, req.source_link)
    except llm.LLMUnavailable as e:
        raise HTTPException(503, f"Model is not running: {e}")
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/opportunities", response_model=Opportunity, status_code=201)
def add_opportunity(opp: Opportunity):
    try:
        store.save_opportunity(opp)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return opp
