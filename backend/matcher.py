"""Plain-code matching. No AI here on purpose: rules are fast, free and predictable.
PERSON B owns this file.

Two outputs:
  match()        opportunities the student qualifies for, ranked
  near_misses()  opportunities that fail exactly ONE of level / course (not yet eligible)
"""
from datetime import date
from typing import List, Optional

from .models import Match, NearMiss, Opportunity, StudentProfile


def _words(text: str) -> set:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(w) > 2}


def _level_ok(profile: StudentProfile, opp: Opportunity) -> bool:
    return not (opp.levels and profile.level and profile.level not in opp.levels)


def _field_ok(profile: StudentProfile, opp: Opportunity) -> bool:
    if opp.fields and profile.course:
        return bool(_words(profile.course) & set().union(*[_words(f) for f in opp.fields]))
    return True


def _usable(profile: StudentProfile, opp: Opportunity, today: date, include_examples: bool) -> bool:
    """Rules that are never 'near misses': placeholders, expired, or the wrong type of thing."""
    if opp.is_example and not include_examples:
        return False
    if opp.deadline and opp.deadline < today:
        return False
    if profile.looking_for and opp.type not in profile.looking_for:
        return False
    return True


def match(profile: StudentProfile, opportunities: List[Opportunity],
          today: Optional[date] = None, include_examples: bool = False) -> List[Match]:
    today = today or date.today()
    results: List[Match] = []
    for opp in opportunities:
        if not _usable(profile, opp, today, include_examples):
            continue
        if not (_level_ok(profile, opp) and _field_ok(profile, opp)):
            continue

        # --- soft score: higher = better fit ---
        score, reasons = 0, []
        if opp.levels and profile.level in opp.levels:
            score += 2
            reasons.append(f"Open to level {profile.level}")
        if opp.fields and profile.course:
            score += 2
            reasons.append(f"Relevant to {profile.course}")
        text_words = _words(" ".join([opp.name, opp.eligibility_text, " ".join(opp.fields)]))
        hits = [i for i in profile.interests if _words(i) & text_words]
        if hits:
            score += len(hits)
            reasons.append("Matches your interest in " + ", ".join(hits))
        if opp.deadline:
            days = (opp.deadline - today).days
            reasons.append(f"Deadline in {days} day{'s' if days != 1 else ''} ({opp.deadline})")
            if days <= 14:
                score += 1
        else:
            reasons.append("No deadline stated: check the official page")
        results.append(Match(opportunity=opp, score=score, reasons=reasons))

    results.sort(key=lambda m: (-m.score, m.opportunity.deadline or date.max))
    return results


def near_misses(profile: StudentProfile, opportunities: List[Opportunity],
                today: Optional[date] = None, include_examples: bool = False) -> List[NearMiss]:
    """Opportunities that fail exactly one of the level / course rules.
    Failing both is too far away to be useful, so those are left out."""
    today = today or date.today()
    results: List[NearMiss] = []
    for opp in opportunities:
        if not _usable(profile, opp, today, include_examples):
            continue
        level_ok, field_ok = _level_ok(profile, opp), _field_ok(profile, opp)
        if level_ok == field_ok:          # both ok = a real match; both fail = too far
            continue
        if not level_ok:
            gap = f"Open to level {', '.join(opp.levels)}; you are at level {profile.level}."
            step = ("Check the official page for when you become eligible or for the next intake, "
                    "and look for similar opportunities open to your level.")
        else:
            gap = f"Open to students in {', '.join(opp.fields)}; your course is {profile.course}."
            step = ("Check the official page to see whether your course can still apply, "
                    "and look for similar opportunities open to your course.")
        results.append(NearMiss(opportunity=opp, gaps=[gap], next_step=step))

    results.sort(key=lambda n: (n.opportunity.deadline or date.max, n.opportunity.name))
    return results
