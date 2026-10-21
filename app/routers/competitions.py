from __future__ import annotations

from fastapi import APIRouter, status

from app.db import Conn
from app.repositories import competitions
from app.schemas import (
    CompetitionCreate,
    CompetitionDetail,
    CompetitionOut,
    CompetitionStats,
    CompetitionStatus,
    CompetitionUpdate,
    EventCreate,
    EventOut,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionOut])
def list_competitions(
    conn: Conn, status: CompetitionStatus | None = None, q: str | None = None
) -> list[CompetitionOut]:
    return competitions.list_competitions(conn, status=status, q=q)


@router.post("", response_model=CompetitionOut, status_code=status.HTTP_201_CREATED)
def create_competition(data: CompetitionCreate, conn: Conn) -> CompetitionOut:
    return competitions.create_competition(conn, data)


@router.get("/{competition_id}", response_model=CompetitionDetail)
def get_competition(competition_id: int, conn: Conn) -> CompetitionDetail:
    return competitions.get_competition_detail(conn, competition_id)


@router.get(
    "/{competition_id}/stats",
    response_model=CompetitionStats,
    summary="Compter les épreuves, inscriptions confirmées et résultats d'une compétition",
)
def get_competition_stats(competition_id: int, conn: Conn) -> CompetitionStats:
    return competitions.get_competition_stats(conn, competition_id)


@router.patch("/{competition_id}", response_model=CompetitionOut)
def update_competition(competition_id: int, data: CompetitionUpdate, conn: Conn) -> CompetitionOut:
    return competitions.update_competition(conn, competition_id, data)


@router.post(
    "/{competition_id}/events", response_model=EventOut, status_code=status.HTTP_201_CREATED
)
def create_event(competition_id: int, data: EventCreate, conn: Conn) -> EventOut:
    return competitions.create_event(conn, competition_id, data)
