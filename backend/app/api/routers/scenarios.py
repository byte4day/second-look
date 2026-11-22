from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import DbSession
from app.models.entities import DrillTurn
from app.schemas.drill import (
    DrillCreate,
    DrillFinishRequest,
    DrillSessionOut,
    DrillTurnOut,
    DrillTurnRequest,
    ScenarioOut,
)
from app.schemas.errors import error_detail
from app.services import scenario_service

router = APIRouter(tags=["scenarios", "drills"])


@router.get("/api/scenarios", response_model=list[ScenarioOut])
def list_scenarios():
    return [ScenarioOut.model_validate(s) for s in scenario_service.list_scenarios()]


@router.post("/api/drills", response_model=DrillSessionOut)
def create_drill(body: DrillCreate, db: DbSession):
    try:
        session = scenario_service.create_drill(db, body.scenario_id, body.difficulty, body.mode)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=error_detail("unknown_scenario", "Scenario not found."),
        ) from None
    return _session_out(db, session)


@router.post("/api/drills/{session_id}/turns")
def drill_turn(session_id: str, body: DrillTurnRequest, db: DbSession):
    try:
        user_turn, bot_turn, finished, warning = scenario_service.add_turn(
            db, session_id, body.message
        )
    except ValueError as exc:
        code = str(exc)
        if code == "drill_ended":
            raise HTTPException(
                status_code=400,
                detail=error_detail("drill_ended", "This practice has already ended."),
            ) from None
        raise HTTPException(
            status_code=404,
            detail=error_detail("invalid_session", "Practice session not found."),
        ) from None
    return {
        "user_turn": DrillTurnOut.model_validate(user_turn),
        "caller_turn": DrillTurnOut.model_validate(bot_turn) if bot_turn else None,
        "finished": finished,
        "warning": warning,
    }


@router.post("/api/drills/{session_id}/finish")
def finish_drill(session_id: str, body: DrillFinishRequest, db: DbSession):
    try:
        return scenario_service.finish_drill(db, session_id, body.hung_up)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=error_detail("invalid_session", "Practice session not found."),
        ) from None


def _session_out(db, session):
    turns = list(
        db.scalars(select(DrillTurn).where(DrillTurn.session_id == session.id).order_by(DrillTurn.id))
    )
    return DrillSessionOut(
        id=session.id,
        scenario_id=session.scenario_id,
        difficulty=session.difficulty,
        mode=session.mode,
        status=session.status,
        turn_count=session.turn_count,
        turns=[DrillTurnOut.model_validate(t) for t in turns],
    )
