"""Drill and scenario schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScenarioOut(BaseModel):
    id: str
    title: str
    plain_description: str
    scammer_goal: str
    opening_message: str
    tactics: list[str]
    payment_method: str
    red_flags_expected: list[str]
    difficulty_variants: dict[str, Any]
    max_turns: int


class DrillCreate(BaseModel):
    scenario_id: str
    difficulty: Literal["easy", "hard"] = "easy"
    mode: Literal["experience", "helper"] = "experience"


class DrillTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class DrillFinishRequest(BaseModel):
    hung_up: bool = False


class DrillTurnOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DrillSessionOut(BaseModel):
    id: str
    scenario_id: str
    difficulty: str
    mode: str
    status: str
    turn_count: int
    turns: list[DrillTurnOut] = Field(default_factory=list)


class DebriefMoment(BaseModel):
    turn_index: int
    quote: str
    flag: str
    why: str


class DebriefOut(BaseModel):
    summary_plain: str = "Here is what happened."
    moments: list[DebriefMoment] = Field(default_factory=list)
    what_you_did_well: list[str] = Field(default_factory=list)
    one_thing_to_try: str = "Hang up and call back using a number you already know."
    hung_up_early: bool = False
