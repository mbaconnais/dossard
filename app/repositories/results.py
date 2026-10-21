from __future__ import annotations

import csv
import io
import sqlite3
from datetime import UTC, datetime

from app.errors import ConflictError, NotFoundError
from app.repositories.common import fetch_or_404
from app.schemas import ResultOut, ResultUnit


def record_result(conn: sqlite3.Connection, registration_id: int, performance: float) -> ResultOut:
    registration = conn.execute(
        "SELECT r.id, r.status, c.status AS competition_status"
        " FROM registrations r"
        " JOIN events e ON e.id = r.event_id"
        " JOIN competitions c ON c.id = e.competition_id"
        " WHERE r.id = ?",
        (registration_id,),
    ).fetchone()
    if registration is None:
        raise NotFoundError(f"Inscription {registration_id} introuvable")
    if registration["status"] != "confirmed" or registration["competition_status"] != "closed":
        raise ConflictError(
            "Résultat possible seulement sur une inscription confirmée d'une compétition close",
            code="results_not_allowed",
        )

    recorded_at = datetime.now(UTC)
    conn.execute(
        "INSERT INTO results (registration_id, performance, recorded_at) VALUES (?, ?, ?)"
        " ON CONFLICT (registration_id) DO UPDATE"
        " SET performance = excluded.performance, recorded_at = excluded.recorded_at",
        (registration_id, performance, recorded_at.isoformat()),
    )
    return ResultOut(
        registration_id=registration_id, performance=performance, recorded_at=recorded_at
    )


def get_event(conn: sqlite3.Connection, event_id: int) -> sqlite3.Row:
    return fetch_or_404(
        conn, "SELECT * FROM events WHERE id = ?", (event_id,), f"Épreuve {event_id} introuvable"
    )


def ranking_rows(conn: sqlite3.Connection, event_id: int) -> list[sqlite3.Row]:
    """Inscriptions confirmées de l'épreuve qui ont un résultat."""
    return conn.execute(
        "SELECT r.bib, r.athlete_id, a.last_name, a.first_name, a.club, res.performance"
        " FROM results res"
        " JOIN registrations r ON r.id = res.registration_id"
        " JOIN athletes a ON a.id = r.athlete_id"
        " WHERE r.event_id = ? AND r.status = 'confirmed'"
        " ORDER BY r.bib",
        (event_id,),
    ).fetchall()


def export_csv(conn: sqlite3.Connection, competition_id: int) -> str:
    competition = conn.execute(
        "SELECT * FROM competitions WHERE id = ?", (competition_id,)
    ).fetchone()
    if competition is None:
        raise NotFoundError(f"Compétition {competition_id} introuvable")

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        [
            "competition",
            "event",
            "unit",
            "bib",
            "first_name",
            "last_name",
            "birth_date",
            "sex",
            "club",
            "license_number",
            "medical_certificate_valid_until",
            "performance",
        ]
    )
    events = conn.execute(
        "SELECT * FROM events WHERE competition_id = ? ORDER BY id", (competition_id,)
    ).fetchall()
    for event in events:
        rows = conn.execute(
            "SELECT r.bib, a.*, res.performance FROM results res"
            " JOIN registrations r ON r.id = res.registration_id"
            " JOIN athletes a ON a.id = r.athlete_id"
            " WHERE r.event_id = ? AND r.status = 'confirmed' ORDER BY r.bib",
            (event["id"],),
        ).fetchall()
        for row in rows:
            if event["unit"] in (ResultUnit.TIME_S, ResultUnit.DISTANCE_M):
                performance = str(round(row["performance"], 2))
            else:
                performance = str(int(row["performance"]))
            writer.writerow(
                [
                    competition["name"],
                    event["name"],
                    event["unit"],
                    row["bib"],
                    row["first_name"],
                    row["last_name"],
                    row["birth_date"],
                    row["sex"],
                    row["club"],
                    row["license_number"],
                    row["medical_certificate_valid_until"],
                    performance,
                ]
            )
    return out.getvalue()
