from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from app.categories import age_category
from app.errors import ConflictError, NotFoundError
from app.schemas import RegistrationOut, RegistrationStatus

ALLOWED_TRANSITIONS = {
    (RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED),
    (RegistrationStatus.PENDING, RegistrationStatus.CANCELLED),
    (RegistrationStatus.CONFIRMED, RegistrationStatus.CANCELLED),
}


def _to_registration(row: sqlite3.Row) -> RegistrationOut:
    return RegistrationOut(
        id=row["id"],
        event_id=row["event_id"],
        athlete_id=row["athlete_id"],
        bib=row["bib"],
        status=RegistrationStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_registration(conn: sqlite3.Connection, registration_id: int) -> RegistrationOut:
    row = conn.execute("SELECT * FROM registrations WHERE id = ?", (registration_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Inscription {registration_id} introuvable")
    return _to_registration(row)


def create_registration(
    conn: sqlite3.Connection, event_id: int, athlete_id: int
) -> RegistrationOut:
    event = conn.execute(
        "SELECT e.id, e.category, e.competition_id, c.status AS competition_status,"
        " c.date AS competition_date"
        " FROM events e JOIN competitions c ON c.id = e.competition_id WHERE e.id = ?",
        (event_id,),
    ).fetchone()
    if event is None:
        raise NotFoundError(f"Épreuve {event_id} introuvable")
    athlete = conn.execute("SELECT * FROM athletes WHERE id = ?", (athlete_id,)).fetchone()
    if athlete is None:
        raise NotFoundError(f"Athlète {athlete_id} introuvable")

    if event["competition_status"] != "open":
        raise ConflictError(
            "Les inscriptions ne sont pas ouvertes pour cette compétition",
            code="registration_closed",
        )

    duplicate = conn.execute(
        "SELECT id FROM registrations WHERE event_id = ? AND athlete_id = ? AND status != ?",
        (event_id, athlete_id, RegistrationStatus.CANCELLED.value),
    ).fetchone()
    if duplicate is not None:
        raise ConflictError(f"Athlète {athlete_id} déjà inscrit à l'épreuve {event_id}")

    if event["category"] is not None:
        category = age_category(date.fromisoformat(athlete["birth_date"]))
        if category != event["category"]:
            raise ConflictError(
                f"Catégorie {category.value} incompatible avec l'épreuve {event['category']}",
                code="category_mismatch",
            )

    competition_date = date.fromisoformat(event["competition_date"])
    certificate = athlete["medical_certificate_valid_until"]
    if certificate is None or date.fromisoformat(certificate) < competition_date:
        raise ConflictError(
            "Certificat médical absent ou expiré à la date de la compétition",
            code="medical_certificate_invalid",
        )

    # Un dossard n'est jamais réattribué : les inscriptions annulées comptent.
    last_bib = conn.execute(
        "SELECT MAX(r.bib) FROM registrations r JOIN events e ON e.id = r.event_id"
        " WHERE e.competition_id = ?",
        (event["competition_id"],),
    ).fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO registrations (event_id, athlete_id, bib, status, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            event_id,
            athlete_id,
            (last_bib or 0) + 1,
            RegistrationStatus.PENDING.value,
            datetime.now(UTC).isoformat(),
        ),
    )
    return get_registration(conn, cursor.lastrowid)


def update_registration_status(
    conn: sqlite3.Connection, registration_id: int, status: RegistrationStatus
) -> RegistrationOut:
    current = get_registration(conn, registration_id)
    if (current.status, status) not in ALLOWED_TRANSITIONS:
        raise ConflictError(
            f"Transition {current.status.value} → {status.value} interdite",
            code="invalid_transition",
        )
    conn.execute(
        "UPDATE registrations SET status = ? WHERE id = ?", (status.value, registration_id)
    )
    return get_registration(conn, registration_id)
