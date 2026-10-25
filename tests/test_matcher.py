from datetime import date

from backend.llm import parse_extraction
from backend.matcher import match
from backend.models import Opportunity, StudentProfile
import pytest

TODAY = date(2026, 10, 25)


def opp(**kw):
    base = dict(id="x", name="Test Scholarship", type="scholarship", link="https://example.com")
    base.update(kw)
    return Opportunity(**base)


def test_expired_is_removed():
    assert match(StudentProfile(), [opp(deadline=date(2026, 10, 1))], today=TODAY) == []


def test_no_deadline_is_kept():
    assert len(match(StudentProfile(), [opp()], today=TODAY)) == 1


def test_wrong_level_is_removed():
    p = StudentProfile(level="100")
    assert match(p, [opp(levels=["400"])], today=TODAY) == []


def test_course_match_uses_words():
    p = StudentProfile(course="Computer Science")
    assert len(match(p, [opp(fields=["Computer Science"])], today=TODAY)) == 1
    assert match(p, [opp(fields=["Law"])], today=TODAY) == []


def test_type_filter():
    p = StudentProfile(looking_for=["job"])
    assert match(p, [opp(type="scholarship")], today=TODAY) == []


def test_examples_hidden_by_default():
    assert match(StudentProfile(), [opp(is_example=True)], today=TODAY) == []
    assert len(match(StudentProfile(), [opp(is_example=True)], today=TODAY, include_examples=True)) == 1


def test_urgent_ranks_first():
    p = StudentProfile()
    soon = opp(id="soon", deadline=date(2026, 10, 30))
    later = opp(id="later", deadline=date(2026, 12, 30))
    assert match(p, [later, soon], today=TODAY)[0].opportunity.id == "soon"


def test_parse_extraction_ok():
    raw = '{"name":"A","type":"job","deadline":"2026-11-01","link":"https://a.com","levels":null}'
    o = parse_extraction("Here: " + raw, "id-1")
    assert o.name == "A" and o.levels == [] and o.deadline == date(2026, 11, 1)


def test_parse_extraction_needs_link():
    with pytest.raises(ValueError):
        parse_extraction('{"name":"A","type":"job"}', "id-1")
