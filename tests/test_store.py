
import json
from datetime import date

import pytest

from backend.models import Opportunity
from backend.store import load_opportunities, save_opportunity


def make_opportunity(opp_id="test-001", name="Test Scholarship"):
    return Opportunity(
        id=opp_id,
        name=name,
        type="scholarship",
        organisation="Test Foundation",
        deadline=date(2027, 6, 30),
        eligibility_text="For eligible university students.",
        levels=["300", "400"],
        fields=["Computer Engineering"],
        link="https://example.org/scholarship",
        date_collected=date(2026, 10, 26),
        is_example=False,
    )


def test_load_opportunities(tmp_path):
    opportunity = make_opportunity()
    file_path = tmp_path / "opportunities.json"
    file_path.write_text(
        json.dumps([opportunity.model_dump(mode="json")]),
        encoding="utf-8",
    )

    loaded = load_opportunities(file_path)

    assert len(loaded) == 1
    assert loaded[0].id == "test-001"
    assert loaded[0].name == "Test Scholarship"


def test_save_opportunity(tmp_path):
    file_path = tmp_path / "opportunities.json"
    file_path.write_text("[]", encoding="utf-8")

    opportunity = make_opportunity()
    save_opportunity(opportunity, file_path)

    loaded = load_opportunities(file_path)

    assert len(loaded) == 1
    assert loaded[0].id == "test-001"


def test_duplicate_id_is_rejected(tmp_path):
    file_path = tmp_path / "opportunities.json"
    existing = make_opportunity()
    file_path.write_text(
        json.dumps([existing.model_dump(mode="json")]),
        encoding="utf-8",
    )

    duplicate = make_opportunity(name="Another Scholarship")

    with pytest.raises(ValueError, match="id already exists"):
        save_opportunity(duplicate, file_path)

    loaded = load_opportunities(file_path)
    assert len(loaded) == 1
    assert loaded[0].name == "Test Scholarship"


def test_load_real_opportunities():
    loaded = load_opportunities()

    assert len(loaded) == 5
    assert all(opportunity.is_example is False for opportunity in loaded)
