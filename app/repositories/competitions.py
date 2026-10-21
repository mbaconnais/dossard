from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from app.errors import ConflictError, NotFoundError
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

# Une compétition avance d'un statut à la fois, sans retour en arrière.
NEXT_STATUS = {
    CompetitionStatus.DRAFT: CompetitionStatus.OPEN,
    CompetitionStatus.OPEN: CompetitionStatus.CLOSED,
    CompetitionStatus.CLOSED: CompetitionStatus.FINISHED,
}


def _to_competition(row: sqlite3.Row) -> CompetitionOut:
    return CompetitionOut(
        id=row["id"],
        name=row["name"],
        venue=row["venue"],
        date=date.fromisoformat(row["date"]),
        status=CompetitionStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_event(row: sqlite3.Row) -> EventOut:
    return EventOut(
        id=row["id"],
        competition_id=row["competition_id"],
        name=row["name"],
        unit=row["unit"],
        category=row["category"],
    )


def list_competitions(
    conn: sqlite3.Connection, status: CompetitionStatus | None = None, q: str | None = None
) -> list[CompetitionOut]:
    sql = "SELECT * FROM competitions"
    clauses: list[str] = []
    params: list[str] = []
    if status is not None:
        clauses.append("status = ?")
        params.append(status.value)
    if q:
        clauses.append(f"name LIKE '%{q}%'")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date, id"
    return [_to_competition(row) for row in conn.execute(sql, params)]


def get_competition(conn: sqlite3.Connection, competition_id: int) -> CompetitionOut:
    row = conn.execute("SELECT * FROM competitions WHERE id = ?", (competition_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Compétition {competition_id} introuvable")
    return _to_competition(row)


def get_competition_detail(conn: sqlite3.Connection, competition_id: int) -> CompetitionDetail:
    competition = get_competition(conn, competition_id)
    rows = conn.execute(
        "SELECT * FROM events WHERE competition_id = ? ORDER BY id", (competition_id,)
    ).fetchall()
    return CompetitionDetail(**competition.model_dump(), events=[_to_event(r) for r in rows])


def get_competition_stats(conn: sqlite3.Connection, competition_id: int) -> CompetitionStats:
    get_competition(conn, competition_id)
    # Comme pour le classement (R8), seuls les résultats d'inscriptions confirmées comptent.
    row = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM events WHERE competition_id = :id) AS events,
            (SELECT COUNT(*) FROM registrations r
               JOIN events e ON e.id = r.event_id
              WHERE e.competition_id = :id AND r.status = 'confirmed') AS confirmed_registrations,
            (SELECT COUNT(*) FROM results res
               JOIN registrations r ON r.id = res.registration_id
               JOIN events e ON e.id = r.event_id
              WHERE e.competition_id = :id AND r.status = 'confirmed') AS results
        """,
        {"id": competition_id},
    ).fetchone()
    return CompetitionStats(
        events=row["events"],
        confirmed_registrations=row["confirmed_registrations"],
        results=row["results"],
    )


def create_competition(conn: sqlite3.Connection, data: CompetitionCreate) -> CompetitionOut:
    cursor = conn.execute(
        "INSERT INTO competitions (name, venue, date, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            data.name,
            data.venue,
            data.date.isoformat(),
            CompetitionStatus.DRAFT.value,
            datetime.now(UTC).isoformat(),
        ),
    )
    return get_competition(conn, cursor.lastrowid)


def update_competition(
    conn: sqlite3.Connection, competition_id: int, data: CompetitionUpdate
) -> CompetitionOut:
    current = get_competition(conn, competition_id)
    changes = data.model_dump(exclude_unset=True)
    # Seul le lieu peut être effacé ; un null sur les autres champs ne change rien.
    changes = {k: v for k, v in changes.items() if v is not None or k == "venue"}

    if "status" in changes and NEXT_STATUS.get(current.status) != changes["status"]:
        raise ConflictError(
            f"Transition {current.status.value} → {changes['status'].value} interdite",
            code="invalid_transition",
        )

    if not changes:
        return current
    values = {k: v.isoformat() if isinstance(v, date) else v for k, v in changes.items()}
    assignments = ", ".join(f"{column} = ?" for column in values)
    conn.execute(
        f"UPDATE competitions SET {assignments} WHERE id = ?",
        (*values.values(), competition_id),
    )
    return get_competition(conn, competition_id)


def create_event(conn: sqlite3.Connection, competition_id: int, data: EventCreate) -> EventOut:
    get_competition(conn, competition_id)
    cursor = conn.execute(
        "INSERT INTO events (competition_id, name, unit, category) VALUES (?, ?, ?, ?)",
        (
            competition_id,
            data.name,
            data.unit.value,
            data.category.value if data.category else None,
        ),
    )
    row = conn.execute("SELECT * FROM events WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _to_event(row)
