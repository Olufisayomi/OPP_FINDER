"""All talking to the open-weight model lives here.

Default setup: Ollama running locally (https://ollama.com).
    ollama pull smollm2:360m        
    set MODEL_NAME to match

Two jobs for the model:
  1. extract_opportunity(raw_text): messy announcement -> filled-in record
  2. explain_match(profile, opportunity): plain-English "why you fit / what's missing"

If the model is not running, callers get LLMUnavailable and the app falls back to
the rule-based reasons, so the demo never dies.
"""
import json
import os
import re
from typing import Optional

import requests

from .models import Opportunity, StudentProfile

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "smollm2:360m") 
TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))


class LLMUnavailable(Exception):
    pass


def _chat(system: str, user: str, as_json: bool = False) -> str:
    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0.1},
    }
    if as_json:
        payload["format"] = "json"
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise LLMUnavailable(str(e)) from e


EXTRACT_SYSTEM = """You turn a pasted opportunity announcement into JSON.
Use ONLY facts written in the text. If something is not stated, use null or an empty list.
NEVER invent a deadline, link, or eligibility rule.
Return JSON with exactly these keys:
name, type (scholarship|internship|job|learning), organisation,
deadline (YYYY-MM-DD or null), eligibility_text (short, copied/condensed from the text),
levels (list from: 100,200,300,400,500,postgraduate,graduate; [] if any),
fields (list of courses/areas; [] if any), link (url from the text or null)."""


def parse_extraction(raw_json: str, fallback_id: str, source_link: str = "") -> Opportunity:
    """Turn the model's JSON text into a validated Opportunity. Raises ValueError if unusable."""
    m = re.search(r"\{.*\}", raw_json, re.S)
    if not m:
        raise ValueError("model did not return JSON")
    data = json.loads(m.group(0))
    data["id"] = fallback_id
    data["link"] = data.get("link") or source_link
    if not data["link"]:
        raise ValueError("no link found: add the official source link by hand")
    for key in ("name", "type"):
        if not data.get(key):
            raise ValueError(f"model did not find '{key}'")
    data["levels"] = data.get("levels") or []
    data["fields"] = data.get("fields") or []
    data["eligibility_text"] = data.get("eligibility_text") or ""
    data["organisation"] = data.get("organisation") or ""
    return Opportunity(**data)


def extract_opportunity(raw_text: str, fallback_id: str, source_link: str = "") -> Opportunity:
    out = _chat(EXTRACT_SYSTEM, raw_text, as_json=True)
    return parse_extraction(out, fallback_id, source_link)


EXPLAIN_SYSTEM = """You help a Nigerian university student understand an opportunity.
Use ONLY the information given. Do not invent requirements, amounts or dates.
In simple English, under 90 words, write three short parts:
Why you may fit: ...
What to check or prepare: ...
Next step: ...
If information is missing, say 'check the official page' instead of guessing."""


def explain_match(profile: StudentProfile, opp: Opportunity) -> str:
    user = (
        f"Student: course={profile.course}, level={profile.level}, interests={profile.interests}\n"
        f"Opportunity: {opp.name} ({opp.type}) by {opp.organisation}\n"
        f"Deadline: {opp.deadline}\nRules: {opp.eligibility_text}"
    )
    return _chat(EXPLAIN_SYSTEM, user).strip()
