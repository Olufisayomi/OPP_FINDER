from datetime import date
from unittest import mock

import pytest

from backend import llm, main
from backend.llm import gap_prompt, parse_extraction
from backend.matcher import match, near_misses
from backend.models import Opportunity, StudentProfile
from backend.render import to_markdown

TODAY = date(2026, 10, 25)


def opp(**kw):
    base = dict(id="x", name="Test Scholarship", type="scholarship", link="https://example.com")
    base.update(kw)
    return Opportunity(**base)


# ---------- matching ----------
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


# ---------- near misses ("not eligible yet") ----------
def test_level_gap_is_a_near_miss():
    p = StudentProfile(course="Law", level="200")
    out = near_misses(p, [opp(levels=["300", "400"])], today=TODAY)
    assert len(out) == 1
    assert "300" in out[0].gaps[0] and "200" in out[0].gaps[0]
    assert out[0].next_step


def test_course_gap_is_a_near_miss_only_with_shared_interest():
    o = opp(fields=["Computer Science"])
    with_interest = StudentProfile(course="Accounting", level="300", interests=["computer"])
    out = near_misses(with_interest, [o], today=TODAY)
    assert len(out) == 1 and "Computer Science" in out[0].gaps[0]
    no_interest = StudentProfile(course="Nursing", level="300", interests=["health"])
    assert near_misses(no_interest, [o], today=TODAY) == []
    assert near_misses(StudentProfile(course="Nursing", level="300"), [o], today=TODAY) == []


def test_two_gaps_is_too_far():
    p = StudentProfile(course="Accounting", level="100")
    assert near_misses(p, [opp(levels=["400"], fields=["Computer Science"])], today=TODAY) == []


def test_real_match_is_not_a_near_miss():
    p = StudentProfile(course="Computer Science", level="300")
    o = opp(levels=["300"], fields=["Computer Science"])
    assert len(match(p, [o], today=TODAY)) == 1
    assert near_misses(p, [o], today=TODAY) == []


def test_expired_wrong_type_and_examples_are_never_near_misses():
    p = StudentProfile(course="Law", level="200", looking_for=["scholarship"])
    assert near_misses(p, [opp(levels=["400"], deadline=date(2026, 1, 1))], today=TODAY) == []
    assert near_misses(p, [opp(type="job", levels=["400"])], today=TODAY) == []
    assert near_misses(p, [opp(levels=["400"], is_example=True)], today=TODAY) == []


def test_no_profile_details_means_no_near_misses():
    assert near_misses(StudentProfile(), [opp(levels=["400"], fields=["Law"])], today=TODAY) == []


def test_gap_prompt_contains_the_gap():
    o = opp(levels=["300"])
    text = gap_prompt(StudentProfile(course="Law", level="200"), o, ["Open to level 300; you are at level 200."])
    assert "does NOT currently meet" in text and "level 300" in text


# ---------- model output cleaning ----------
def test_parse_extraction_ok():
    raw = '{"name":"A","type":"job","deadline":"2026-11-01","link":"https://a.com","levels":null}'
    o = parse_extraction("Here: " + raw, "id-1")
    assert o.name == "A" and o.levels == [] and o.deadline == date(2026, 11, 1)


def test_parse_extraction_needs_link():
    with pytest.raises(ValueError):
        parse_extraction('{"name":"A","type":"job"}', "id-1")


def test_parse_extraction_none_text_becomes_empty():
    raw = '{"name":"A","type":"Scholarship","deadline":"None","link":"https://a.com","levels":"None","fields":"Law"}'
    o = parse_extraction(raw, "id-1")
    assert o.deadline is None and o.levels == [] and o.fields == ["Law"] and o.type == "scholarship"


# ---------- API logic (calls the function directly) ----------
def _items():
    return [
        opp(id="fit", name="Fits", levels=["300"], fields=["Law"]),
        opp(id="gap", name="Needs 400", levels=["400"], fields=["Law"]),
    ]


def test_api_match_without_model():
    req = main.MatchRequest(profile=StudentProfile(course="Law", level="300"), explain=False)
    with mock.patch.object(main.store, "load_opportunities", return_value=_items()):
        res = main.match(req)
    assert [m.opportunity.id for m in res.matches] == ["fit"]
    assert [n.opportunity.id for n in res.near_misses] == ["gap"]
    assert res.near_misses[0].explanation == ""


def test_api_match_survives_model_failure():
    req = main.MatchRequest(profile=StudentProfile(course="Law", level="300"))
    with mock.patch.object(main.store, "load_opportunities", return_value=_items()), \
            mock.patch.object(main.llm, "_chat", side_effect=llm.LLMUnavailable("down")):
        res = main.match(req)
    assert res.matches[0].explanation == "" and res.near_misses[0].explanation == ""
    assert res.near_misses[0].next_step


def test_api_match_uses_model_text():
    req = main.MatchRequest(profile=StudentProfile(course="Law", level="300"))
    with mock.patch.object(main.store, "load_opportunities", return_value=_items()), \
            mock.patch.object(main.llm, "_chat", return_value="MODEL TEXT"):
        res = main.match(req)
    assert res.matches[0].explanation == "MODEL TEXT" and res.near_misses[0].explanation == "MODEL TEXT"


# ---------- screen text ----------
def test_markdown_has_both_sections():
    req = main.MatchRequest(profile=StudentProfile(course="Law", level="300"), explain=False)
    with mock.patch.object(main.store, "load_opportunities", return_value=_items()):
        data = main.match(req).model_dump(mode="json")
    md = to_markdown(data)
    assert "You can apply for these" in md and "Not eligible yet" in md
    assert "Fits" in md and "Needs 400" in md and "Verify on the official page" in md


def test_markdown_empty():
    assert "No open opportunities" in to_markdown({"matches": [], "near_misses": []})
