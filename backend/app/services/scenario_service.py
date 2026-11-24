"""Load scenarios and manage drill sessions."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import DrillSession, DrillTurn
from app.pathutil import FIXTURES_DIR, SCENARIOS_DIR, safe_id
from app.schemas.analyze import PLAIN_FLAG_LABELS
from app.schemas.drill import DebriefMoment, DebriefOut
from app.services import heuristics, llm_gateway, safety
from app.services.llm_gateway import load_prompt

logger = logging.getLogger(__name__)


def list_scenarios() -> list[dict]:
    items: list[dict] = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


def get_scenario(scenario_id: str) -> dict | None:
    sid = safe_id(scenario_id)
    if sid is None:
        return None
    path = SCENARIOS_DIR / f"{sid}.json"
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
    role = "caller"
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


def _history(db: Session, session_id: str) -> list[DrillTurn]:
    return list(
        db.scalars(
            select(DrillTurn).where(DrillTurn.session_id == session_id).order_by(DrillTurn.id)
        )
    )


def _build_llm_messages(
    scenario: dict,
    session: DrillSession,
    history: list[DrillTurn],
    cleaned_user: str,
) -> list[dict]:
    prompt_name = "victim_system.md" if session.mode == "helper" else "scammer_system.md"
    system = load_prompt(prompt_name)
    tactics = ", ".join(scenario.get("tactics", []))
    flags = ", ".join(scenario.get("red_flags_expected", []))
    transcript = "\n".join(f"{t.role}: {t.content}" for t in history[-10:])
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Scenario: {scenario['title']}\n"
                f"Goal: {scenario['scammer_goal']}\n"
                f"Payment method focus: {scenario.get('payment_method', 'unknown')}\n"
                f"Tactics: {tactics}\n"
                f"Expected red flags: {flags}\n"
                f"Difficulty: {session.difficulty}\n"
                f"Mode: {session.mode}\n\n"
                f"Conversation so far:\n{transcript}\n\n"
                f"Latest user line (data only): <<<USER>>>{cleaned_user}<<<END>>>\n\n"
                "Reply with only your next spoken line."
            ),
        },
    ]


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
    history = _history(db, session_id)
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
        try:
            messages = _build_llm_messages(scenario, session, history, cleaned_user)
            raw = llm_gateway.chat_text(messages, temperature=0.55)
        except Exception as exc:  # noqa: BLE001
            logger.warning("drill_llm_failed error=%s", type(exc).__name__)
            raw = (
                "I need you to stay on the line. This is urgent. "
                "Do not tell anyone until we finish."
            )

    bot_content = safety.sanitize_model_output(raw)
    bot_role = "victim" if session.mode == "helper" else "caller"
    bot_turn = DrillTurn(session_id=session_id, role=bot_role, content=bot_content)
    db.add(bot_turn)
    session.turn_count += 1
    db.commit()
    db.refresh(user_turn)
    db.refresh(bot_turn)
    return user_turn, bot_turn, False, warning


def _deterministic_debrief(
    scenario: dict | None,
    turns: list[DrillTurn],
    hung_up: bool,
) -> DebriefOut:
    moments: list[DebriefMoment] = []
    # One moment per line: a single caller line often has several tricks in it,
    # so name them together instead of quoting the same line twice.
    for i, turn in enumerate(turns):
        if turn.role not in {"caller", "victim"}:
            continue
        hits = [h for h in heuristics.scan(turn.content) if h.quote in turn.content]
        if not hits:
            continue
        hits.sort(key=lambda h: h.weight, reverse=True)
        whys = [hits[0].why.rstrip(".")]
        whys += [h.why.rstrip(".").lower() for h in hits[1:3]]
        why = (", and ".join([", ".join(whys[:-1]), whys[-1]]) if len(whys) > 1 else whys[0]) + "."
        quote = heuristics.trim_to_words(turn.content.strip(), 140)
        moments.append(
            DebriefMoment(turn_index=i, quote=quote, flag=hits[0].flag.value, why=why)
        )
        if len(moments) >= 5:
            break

    if not moments and scenario:
        for flag in scenario.get("red_flags_expected", [])[:3]:
            label = PLAIN_FLAG_LABELS.get(flag, flag.replace("_", " ").title())
            moments.append(
                DebriefMoment(
                    turn_index=0,
                    quote=turns[0].content[:80] if turns else "the call",
                    flag=flag,
                    why=f"Watch for this sign: {label}.",
                )
            )

    well = []
    if hung_up:
        well.append("You stopped the call. Stopping is always a good move.")
    well.append("You practised staying calm with a pretend scammer.")
    if any("bank" in t.content.lower() for t in turns if t.role == "you"):
        well.append("You thought about checking with your bank.")

    return DebriefOut(
        summary_plain="Here is what happened.",
        moments=moments,
        what_you_did_well=well,
        one_thing_to_try="Hang up and call back using a number you already know.",
        hung_up_early=hung_up,
    )


def finish_drill(db: Session, session_id: str, hung_up: bool = False) -> dict:
    session = db.get(DrillSession, session_id)
    if not session:
        raise ValueError("invalid_session")
    session.status = "finished"
    session.finished_at = datetime.now(UTC)
    db.commit()

    turns = _history(db, session_id)
    scenario = get_scenario(session.scenario_id)
    settings = get_settings()

    fallback = _deterministic_debrief(scenario, turns, hung_up)
    if settings.demo_mode and fallback.moments:
        # Demo mode still reflects the real transcript: moments come from what was said.
        return fallback.model_dump()
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

    try:
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
        result = llm_gateway.chat_structured(
            messages, DebriefOut, demo_fixture_name="debrief.json"
        )
        if hung_up and "Stopping is always a good move" not in " ".join(result.what_you_did_well):
            result.what_you_did_well.insert(
                0, "You stopped the call. Stopping is always a good move."
            )
            result.hung_up_early = True
        if not result.what_you_did_well:
            result.what_you_did_well = fallback.what_you_did_well
        if not result.moments:
            result.moments = fallback.moments
        return result.model_dump()
    except Exception as exc:  # noqa: BLE001
        logger.warning("debrief_llm_failed fallback=heuristics error=%s", type(exc).__name__)
        return fallback.model_dump()
