"""Génère une page HTML du classement d'une épreuve.

Usage, depuis la racine du dépôt, venv activé :
    python scripts/classement_html.py <event_id>

Le classement vient de l'API (GET /events/{event_id}/ranking), appelée en interne sans
serveur : la page montre exactement ce que renvoie l'API. Le nom et l'unité de l'épreuve
sont lus dans la base (variable DOSSARD_DB, sinon data/dossard.db).
Écrit classement-<event_id>.html dans le répertoire courant.
"""

from __future__ import annotations

import html
import sqlite3
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*httpx.*")  # avertissement de Starlette sur httpx

from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_db_path  # noqa: E402
from app.main import app  # noqa: E402

MARKER = "<!-- Généré par classement_html.py (skill classement-html) -->"
UNITS = {"time_s": "s", "distance_m": "m", "points": "pts"}


def render(event_name: str, unit: str, entries: list[dict]) -> str:
    rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{} {}</td></tr>".format(
            e["rank"],
            e["bib"],
            html.escape(f"{e['first_name']} {e['last_name']}"),
            html.escape(e["club"] or ""),
            e["performance"],
            UNITS.get(unit, ""),
        )
        for e in entries
    )
    return f"""<!doctype html>
{MARKER}
<html lang="fr">
<head><meta charset="utf-8"><title>Classement : {html.escape(event_name)}</title>
<style>body{{font-family:sans-serif;margin:2rem}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:.3rem .8rem}}th{{background:#1b1f2a;color:#fff}}</style>
</head>
<body>
<h1>Classement : {html.escape(event_name)}</h1>
<table>
<tr><th>Rang</th><th>Dossard</th><th>Athlète</th><th>Club</th><th>Performance</th></tr>
{rows}
</table>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Usage : classement_html.py <event_id>", file=sys.stderr)
        return 2
    event_id = int(sys.argv[1])
    db_path = get_db_path()
    if not db_path.exists():
        print(f"Base introuvable : {db_path}. Lancez scripts/seed.py --reset", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    try:
        event = conn.execute("SELECT name, unit FROM events WHERE id = ?", (event_id,)).fetchone()
    finally:
        conn.close()
    if event is None:
        print(f"Épreuve {event_id} introuvable", file=sys.stderr)
        return 1

    response = TestClient(app).get(f"/events/{event_id}/ranking")
    if response.status_code != 200:
        print(
            f"Classement indisponible ({response.status_code}) : {response.text}", file=sys.stderr
        )
        return 1
    body = response.json()
    entries = body["data"] if isinstance(body, dict) else body  # enveloppe ou liste nue

    out = Path.cwd() / f"classement-{event_id}.html"
    out.write_text(render(event[0], event[1], entries), encoding="utf-8")
    print(f"{out} : {len(entries)} athlètes classés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
