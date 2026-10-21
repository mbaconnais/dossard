from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request, status

from app.db import Conn
from app.errors import ApiError
from app.repositories import athletes
from app.schemas import AthleteCreate, AthleteImportResult, AthleteOut

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.get("", response_model=list[AthleteOut])
def list_athletes(
    conn: Conn,
    club: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AthleteOut]:
    return athletes.list_athletes(conn, club=club, limit=limit, offset=offset)


@router.post("/import", response_model=AthleteImportResult)
async def import_athletes(request: Request, conn: Conn) -> AthleteImportResult:
    try:
        content = (await request.body()).decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ApiError("Le CSV doit être encodé en UTF-8", code="invalid_csv") from None
    return athletes.import_athletes(conn, content)


@router.get("/{athlete_id}", response_model=AthleteOut)
def get_athlete(athlete_id: int, conn: Conn) -> AthleteOut:
    return athletes.get_athlete(conn, athlete_id)


@router.post("", response_model=AthleteOut, status_code=status.HTTP_201_CREATED)
def create_athlete(data: AthleteCreate, conn: Conn) -> AthleteOut:
    return athletes.create_athlete(conn, data)
