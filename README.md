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
5. If a student doesn’t qualify yet, the app doesn’t hide the opportunity. When exactly one rule fails (their level or course), it shows what is missing and suggests next steps, such as checking the official page for the next intake or looking for similar opportunities.

## 3. The model 
- **Model:** SmolLM2-360M-Instruct by Hugging Face (HuggingFaceTB), about 360 million parameters. We run it locally through Ollama as `smollm2:360m` (725 MB download). Source: https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct
- **Licence:** Apache 2.0, checked on 2026-10-27 at the model card above (https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/blob/main/README.md). Open weights are not automatically open source, so we read the licence terms before using the model.
- **Role:** reads a pasted opportunity announcement and drafts a structured record (a person checks it before saving), and writes a short plain-English explanation of why a student may qualify. It is not used for matching decisions: plain-code rules decide who qualifies.
- **Why this model:** it is small enough to run on student laptops with limited memory. We first tried Qwen2.5-1.5B, but it took a while to respond on our laptop and caused the computer to stop responding, so we switched to a smaller model.
- **Known limitations:**
  - The model card says it mainly handles English and may not be factually accurate, so every result links to the official page for confirmation.
  - May misread dates or eligibility rules when drafting records, so drafts are checked by a person.

## 4. Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
Settings are optional environment variables, see .env.example for the names.                              

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

## 7. Technical decisions

- **Rules decide who qualifies; the model only explains and drafts.** Whether a student qualifies (level, course, type, deadline) is decided by plain code in `backend/matcher.py`, because rules are fast, predictable and can be tested. The model never makes that decision, so it can't invent an eligibility rule.
- **A small open-weight model run locally.** We use SmolLM2-360M-Instruct (Apache 2.0) through Ollama, because it can run on student laptops with limited memory and needs no paid service or API keys. We first tried Qwen2.5-1.5B, but it was too slow on our hardware. The trade-off is lower answer quality, which we describe in section 9.
- **Two jobs for the model.** It writes short plain-English explanations for matches, and it explains what is missing for opportunities a student does not qualify for yet. It can also draft a structured record from a pasted announcement.
- **"Not eligible yet" instead of hiding opportunities.** If exactly one rule fails (level or course), the app shows the opportunity with the gap in plain words and a next step. The gap comes from the rules. Only the advice comes from the model.
- **Model output is checked.** Drafted records are validated with Pydantic. The code cleans up common small-model mistakes, such as writing "None" instead of leaving a field empty, and every draft must be reviewed by a person against the official page before it is saved.
- **Real data only.** Opportunities are collected by hand from official pages. Each record needs an official link and the date it was checked. We do not scrape websites. Placeholder records are marked `is_example` and are hidden from students.
- **It still works if the model is slow or down.** If the model does not answer, the app shows the rule-based reasons and next steps instead, so results are never blank.
- **Kept fast on a CPU.** Only the top 3 matches and 2 "not yet" items get a model explanation, replies are capped in length, and the timeout can be changed with `LLM_TIMEOUT`.
- **Simple structure.** FastAPI serves the logic, and a small Gradio screen sits on top, so the API can be used on its own. Data is stored in a JSON file for simplicity. A database such as SQLite is a next step.


## 8. Acknowledgements and AI-assisted work 
- Libraries: FastAPI, Pydantic, Gradio, Requests, Ollama.
- Data sources: list each source page used.
- AI-assisted work: the initial project scaffold was drafted with an AI assistant (Claude) and
  reviewed by the team.

## 9. Known limitations / next steps

### Limitations
- **Small dataset.** Opportunities are collected by hand from official pages, so the list is small (currently 72 number of records) and deadlines change. Always confirm details on the official page linked with each result.
- **Drafting records is unreliable.** In a test where the model drafted a record from an announcement already in our data (the MTN Science and Technology Scholarship), it got 4 of 8 fields right when compared with the record we collected from the official page. It correctly found the name, type and organisation, and correctly left the deadline empty. It got the eligibility rules, the levels, the courses and the link wrong: it put "No deadline stated" in the eligibility field, listed all seven levels instead of 300, 400 and graduate, filled the courses field with `["Computer Science", "300", "AI"]` instead of Science, Technology, Engineering, Mathematics and Medicine, and gave a different link from the official one. It also wrote the word "None" instead of leaving a field empty in an earlier test. Because of this, drafted records are never saved automatically: a person checks each one against the official page first.
- **Matching is simple.** Courses are matched by shared words (for example "Computer" in both "Computer Science" and "Computer Engineering"), so some related courses may be missed or wrongly matched. Interests are matched by keywords, not by meaning.
- **Nigeria-focused and English-only.** Other countries and languages are not supported.
- **No accounts or saved profiles.** Students enter their details each time.
- **Tested lightly.** Automated tests cover the matching rules and cleaning of model output. We tested the screen manually with 12 students.
- **Course and interest can conflict.** The course is treated as a requirement, and interests only rank results. A student whose interests differ from their course (for example a Nursing student interested in writing or software) often gets no matches, because the opportunities that fit their interest list other courses. Opportunities that fit through interest appear only under "Not eligible yet", and only when the interest words overlap with the opportunity's text. Courses are matched by shared words, so related courses such as Nursing and Medicine are not connected.

### Next steps
- Collect more verified opportunities, and add a way to flag expired or incorrect ones.
- Better matching using embeddings (meaning, not just keywords), and support for more details such as state of origin, CGPA and gender-specific schemes.
- Reminders before a deadline.
- Explanations in Pidgin, Yoruba, Igbo and Hausa.
- Try a larger open-weight model on a computer with more memory and compare the quality.
- Replace the JSON file with a database such as SQLite.
- Let students save a profile and track the opportunities they've applied for.
- **Interest-based matching.** Let students choose "match my course" or "match my interests", and use embeddings so related interests are matched by meaning (for example "writing" with "content creation" or "technical writing"). Also record, for each opportunity, whether students from other courses may apply, so the rule is not guessed from the course list.

## Licence
MIT, see `LICENSE`.
