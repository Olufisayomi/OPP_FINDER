"""Plain-code matching. No AI here on purpose: rules are fast, free and predictable.
PERSON B owns this file."""
from datetime import date
from typing import List, Optional

from .models import Match, Opportunity, StudentProfile


def _words(text: str) -> set:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(w) > 2}


def match(profile: StudentProfile, opportunities: List[Opportunity],
          today: Optional[date] = None, include_examples: bool = False) -> List[Match]:
    today = today or date.today()
    results: List[Match] = []
    for opp in opportunities:
        if opp.is_example and not include_examples:
            continue
        # --- hard rules: any failure removes the opportunity ---
        if opp.deadline and opp.deadline < today:
            continue
        if profile.looking_for and opp.type not in profile.looking_for:
            continue
        if opp.levels and profile.level and profile.level not in opp.levels:
            continue
        if opp.fields and profile.course:
            course_words = _words(profile.course)
            if not any(course_words & _words(f) for f in opp.fields):
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
