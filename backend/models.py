"""The two 'forms' the whole app is built around.

Opportunity  = one scholarship / internship / job / course (a "record").
StudentProfile = what a student tells us about themselves.
"""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

OpportunityType = Literal["scholarship", "internship", "job", "learning"]
LEVELS = ["100", "200", "300", "400", "500", "postgraduate", "graduate"]


class Opportunity(BaseModel):
    id: str
    name: str
    type: OpportunityType
    organisation: str = ""
    deadline: Optional[date] = None          # None = no deadline stated
    eligibility_text: str = ""               # the rules in plain words, copied from the source
    levels: List[str] = Field(default_factory=list)   # empty = any level
    fields: List[str] = Field(default_factory=list)   # empty = any course
    link: str                                # OFFICIAL source page. Required.
    date_collected: Optional[date] = None    # when a human last checked it
    is_example: bool = False                 # True = placeholder, never show as real


class StudentProfile(BaseModel):
    course: str = ""                         # e.g. "Computer Science"
    level: str = ""                          # one of LEVELS
    interests: List[str] = Field(default_factory=list)
    looking_for: List[OpportunityType] = Field(default_factory=list)  # empty = all types


class Match(BaseModel):
    opportunity: Opportunity
    score: int
    reasons: List[str]                       # rule-based reasons (always shown)
    explanation: str = ""                    # model-written explanation (may be empty)
