"""Load scenarios and manage drill sessions."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import DrillSession, DrillTurn
from app.pathutil import FIXTURES_DIR, SCENARIOS_DIR
from app.schemas.drill import DebriefOut
from app.services import llm_gateway, safety
from app.services.llm_gateway import load_prompt


def list_scenarios() -> list[dict]:
    items: list[dict] = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


def get_scenario(scenario_id: str) -> dict | None:
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def create_drill(
    db: Session,
    scenario_id: str,
    difficulty: str,
    mode: str,
) -> DrillSession:
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError("unknown_scenario")
    session = DrillSession(
        id=str(uuid.uuid4()),
        scenario_id=scenario_id,
        difficulty=difficulty,
        mode=mode,
        status="active",
        turn_count=0,
    )
    db.add(session)
    variants = scenario.get("difficulty_variants", {})
    opening = variants.get(difficulty, {}).get("opening_message") or scenario["opening_message"]
    role = "victim" if mode == "helper" else "caller"
    if mode == "helper":
        opening = (
            "I just got a worrying call. They said they are from "
            f"{scenario.get('title', 'someone')}. What should I do? "
            f"They told me: {opening}"
        )
        role = "victim"
    db.add(DrillTurn(session_id=session.id, role=role, content=opening))
    session.turn_count = 1
    db.commit()
    db.refresh(session)
    return session


def add_turn(
    db: Session, session_id: str, user_message: str
) -> tuple[DrillTurn, DrillTurn | None, bool, str | None]:
    session = db.get(DrillSession, session_id)
    if not session:
        raise ValueError("invalid_session")
    if session.status != "active":
        raise ValueError("drill_ended")
    scenario = get_scenario(session.scenario_id)
    if not scenario:
        raise ValueError("unknown_scenario")

    warning: str | None = None
    if safety.contains_real_secrets(user_message):
        cleaned_user = "[hidden]"
        warning = "Please do not type real details, even in practice."
    else:
        cleaned_user = safety.sanitize_user_message_for_display(user_message)

    max_turns = int(scenario.get("max_turns", 12))

    if safety.refuses_howto_scam(user_message):
        reply = (
            "I will not help write scams. This practice is only for learning "
            "how to stop them. You can hang up now."
        )
        user_turn = DrillTurn(session_id=session_id, role="you", content=cleaned_user)
        bot_turn = DrillTurn(session_id=session_id, role="caller", content=reply)
        db.add_all([user_turn, bot_turn])
        session.turn_count += 2
        session.status = "finished"
        session.finished_at = datetime.now(UTC)
        db.commit()
        return user_turn, bot_turn, True, warning

    user_turn = DrillTurn(session_id=session_id, role="you", content=cleaned_user)
    db.add(user_turn)
    session.turn_count += 1

    if session.turn_count >= max_turns:
        bot_content = "The call has ended."
        bot_turn = DrillTurn(session_id=session_id, role="caller", content=bot_content)
        db.add(bot_turn)
        session.turn_count += 1
        session.status = "finished"
        session.finished_at = datetime.now(UTC)
        db.commit()
        return user_turn, bot_turn, True, warning

    settings = get_settings()
    if settings.demo_mode:
        turns = json.loads((FIXTURES_DIR / "drill_turns.json").read_text(encoding="utf-8"))
        idx = min(max((session.turn_count - 2) // 2, 0), len(turns) - 1)
        raw = turns[idx].get("caller_reply", "Please stay on the line.")
        if session.mode == "helper":
            raw = turns[idx].get(
                "victim_reply",
                "I am still worried. They want me to pay now. What should I say?",
            )
    else:
        prompt_name = "victim_system.md" if session.mode == "helper" else "scammer_system.md"
        system = load_prompt(prompt_name)
        tactics = ", ".join(scenario.get("tactics", []))
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Scenario: {scenario['title']}. Goal: {scenario['scammer_goal']}. "
                    f"Tactics: {tactics}. Difficulty: {session.difficulty}. "
                    f"Mode: {session.mode}. "
                    f"User said: <<<USER>>>{cleaned_user}<<<END>>>"
                ),
            },
        ]
        raw = llm_gateway.chat_text(messages, temperature=0.5)

    bot_content = safety.sanitize_model_output(raw)
    bot_role = "victim" if session.mode == "helper" else "caller"
    bot_turn = DrillTurn(session_id=session_id, role=bot_role, content=bot_content)
    db.add(bot_turn)
    session.turn_count += 1
    db.commit()
    db.refresh(user_turn)
    db.refresh(bot_turn)
    return user_turn, bot_turn, False, warning


def finish_drill(db: Session, session_id: str, hung_up: bool = False) -> dict:
    session = db.get(DrillSession, session_id)
    if not session:
        raise ValueError("invalid_session")
    session.status = "finished"
    session.finished_at = datetime.now(UTC)
    db.commit()

    settings = get_settings()
    if settings.demo_mode:
        data = json.loads((FIXTURES_DIR / "debrief.json").read_text(encoding="utf-8"))
        if hung_up:
            data = {
                **data,
                "hung_up_early": True,
                "what_you_did_well": [
                    "You stopped the call. Stopping is always a good move.",
                    *data.get("what_you_did_well", []),
                ],
            }
        return DebriefOut.model_validate(data).model_dump()

    scenario = get_scenario(session.scenario_id)
    turns = list(
        db.scalars(select(DrillTurn).where(DrillTurn.session_id == session_id).order_by(DrillTurn.id))
    )
    transcript = "\n".join(f"{t.role}: {t.content}" for t in turns)
    prompt = load_prompt("debrief.md")
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Scenario: {scenario['title'] if scenario else session.scenario_id}.\n"
                f"User hung up early: {hung_up}\nTranscript:\n{transcript}"
            ),
        },
    ]
    result = llm_gateway.chat_structured(messages, DebriefOut, demo_fixture_name="debrief.json")
    if hung_up and "Stopping is always a good move" not in " ".join(result.what_you_did_well):
        result.what_you_did_well.insert(0, "You stopped the call. Stopping is always a good move.")
        result.hung_up_early = True
    if not result.what_you_did_well:
        result.what_you_did_well = ["You took time to practise. That helps you stay ready."]
    return result.model_dump()
