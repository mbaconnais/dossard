# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

API FastAPI + SQLite de gestion de compétitions sportives. Code, messages d'erreur et docs en français.

## Commandes

- Installer : `pip install -e ".[dev]"`
- Tests : `pytest` ; un seul test : `pytest tests/test_results.py::test_nom`
- Lint + format : `ruff check . && ruff format .`
- Données d'exemple : `python scripts/seed.py --reset`
- Serveur : `uvicorn app.main:app --reload`

## Règles

- Lancer `pytest` avant tout commit : les tests doivent être verts.
- Lancer `ruff check . && ruff format .` après toute modification Python.
- Pas de nouvelle dépendance sans demander.
- Ne jamais lire ni afficher `.env` : il contient des secrets.
- `scripts/legacy/` : lecture autorisée, aucune modification ni suppression sans demande explicite.

## Erreurs

- Lever `NotFoundError`, `ConflictError` ou `ApiError(message, code=...)` de `app/errors.py`, jamais `HTTPException`.
- Format de réponse : `{"error": {"code": "...", "message": "..."}}` ; les 422 gardent le format FastAPI.
- `app/routers/results.py` déroge à ces règles : ne pas le prendre pour modèle (suivre `competitions.py`).

## Tests

- Réutiliser les fixtures de `tests/conftest.py` : `client`, `make_competition`, `make_event`, `make_athlete`, `make_registration`.
- Un fichier de test par router (`tests/test_<entité>.py`).
- Toujours tester les cas d'erreur : 404, 409, 422.

## Documentation

- Toute route ajoutée ou modifiée : une ligne dans `docs/api.md`.
- Et une entrée en tête de `CHANGELOG.md`, section « Non publié » (créer le fichier s'il n'existe pas).
