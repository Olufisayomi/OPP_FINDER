# OppFinder

Helps university students in Nigeria find scholarships, internships, jobs and learning
opportunities they may qualify for, and explains in plain English why, what to prepare,
and the deadline. Built for OPEN//BUILD 2026 (OSCA Ile-Ife, Hacktoberfest 2026).

> **Status:** early prototype. Opportunity data is collected by hand from official pages.
> Always confirm details on the official link shown with each result.

## 1. The problem  (TODO: fill in with what 3 students told you)
- Who: ...
- What goes wrong today: ...
- Why it matters: ...

## 2. How it works
1. A student enters course, level, interests and what they want.
2. Plain-code **rules** remove anything expired or not open to them and rank the rest.
3. The **open-weight model** writes a short "why you may fit / what to prepare / next step".
4. A separate team feature lets us paste a messy announcement and the model drafts a
   structured record, which a human checks before saving.

## 3. The model  (TODO: complete before submitting)
- Model: `...` (size, source)
- **Licence:** `...`  — checked on (date) at (link). Open weights are not automatically open source.
- Role: extraction of records + explanations. Not used for matching decisions.
- Why this model: ...
- Known limitations: may misread dates, may be wrong on rules, slower on a laptop CPU.

## 4. Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then edit if needed

# the model (needs https://ollama.com installed)
ollama pull smollm2:360m       

uvicorn backend.main:app --reload     # API + test page at http://localhost:8000/docs
python app.py                         # student screen (second terminal)
```
Run tests: `pytest`

## 5. Project layout
```
backend/models.py    the two "forms": Opportunity (record) and StudentProfile
backend/store.py     reads/writes data/opportunities.json
backend/matcher.py   rule-based matching and ranking (no AI)
backend/llm.py       everything that talks to the model
backend/main.py      the API endpoints
app.py               simple Gradio screen
data/                the opportunity records (real ones need a link + date_collected)
tests/               tests for matching and model-output parsing
```

## 6. Data rules
- Every record needs the **official link** and the date a human last checked it.
- Records with `"is_example": true` are placeholders and never shown to students by default.
- No scraping; no private or personal data in this repo; no API keys (use `.env`, which is git-ignored).

## 7. Technical decisions  (TODO)
- Rules decide who qualifies; the model only explains and extracts, because rules are predictable.
- Model output is validated and drafts are human-reviewed before saving.
- ...

## 8. Acknowledgements and AI-assisted work  (TODO: be specific)
- Libraries: FastAPI, Pydantic, Gradio, Requests, Ollama.
- Data sources: list each source page used.
- AI-assisted work: the initial project scaffold was drafted with an AI assistant (Claude) and
  reviewed by the team. List anything else significant.

## 9. Known limitations / next steps
- Small hand-collected dataset; deadlines change.
- Matching is keyword-based; better matching (embeddings) is a next step.

## Licence
MIT, see `LICENSE`.
