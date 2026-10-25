"""Tiny storage layer: one JSON file. PERSON A: swap this for SQLite if you want.
Keep the function names so the rest of the app doesn't change."""
import json
from pathlib import Path
from typing import List

from .models import Opportunity

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "opportunities.json"


def load_opportunities(path: Path = DATA_FILE) -> List[Opportunity]:
    with open(path, encoding="utf-8") as f:
        return [Opportunity(**row) for row in json.load(f)]


def save_opportunity(opp: Opportunity, path: Path = DATA_FILE) -> None:
    items = load_opportunities(path)
    if any(o.id == opp.id for o in items):
        raise ValueError(f"id already exists: {opp.id}")
    items.append(opp)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([o.model_dump(mode="json") for o in items], f, indent=2, ensure_ascii=False)
