"""The API. Run:  uvicorn backend.main:app --reload   then open http://localhost:8000/docs
That /docs page is a free test screen for every endpoint."""
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import llm, matcher, store
from .models import MatchResponse, Opportunity, StudentProfile

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
    limit: int = 3                # only the top N matches get a model explanation (keeps it fast)
    gap_limit: int = 2            # only the first N "not yet eligible" items get a model explanation
    include_examples: bool = False


@app.post("/match", response_model=MatchResponse)
def match(req: MatchRequest):
    """Returns two lists: opportunities the student qualifies for, and 'near misses'
    (not eligible yet, with what is missing and what to do next)."""
    items = store.load_opportunities()
    matches = matcher.match(req.profile, items, include_examples=req.include_examples)
    near = matcher.near_misses(req.profile, items, include_examples=req.include_examples)
    if req.explain:
        for m in matches[: req.limit]:
            try:
                m.explanation = llm.explain_match(req.profile, m.opportunity)
            except llm.LLMUnavailable:
                m.explanation = ""   # the screen still shows the rule-based reasons
        for n in near[: req.gap_limit]:
            try:
                n.explanation = llm.explain_gap(req.profile, n.opportunity, n.gaps)
            except llm.LLMUnavailable:
                n.explanation = ""   # the screen falls back to the rule-based next step
    return MatchResponse(matches=matches, near_misses=near)


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
