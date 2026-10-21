# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Dossard : API FastAPI + SQLite de gestion de compétitions sportives (compétitions, épreuves, athlètes, inscriptions, résultats). Projet fil rouge d'une formation Claude Code ; code, commentaires, docstrings et messages d'erreur sont en français.

## Commandes

```bash
pip install -e ".[dev]"             # installation (Python ≥ 3.12, venv dans .venv)
pytest                              # tous les tests (doivent être verts avant tout commit)
pytest tests/test_results.py::test_nom   # un seul test
ruff check . && ruff format .       # lint + formatage (line-length 100, règles E F I UP B ANN)
python scripts/seed.py [--reset]    # données synthétiques dans data/dossard.db
uvicorn app.main:app --reload       # serveur sur :8000, doc interactive sur /docs
```

## Architecture

Trois couches par entité (competitions, athletes, registrations, results), un module chacune :

- `app/routers/<entité>.py` : endpoints FastAPI minces, la connexion arrive via la dépendance `Conn` (`app/db.py`).
- `app/repositories/<entité>.py` : SQL brut `sqlite3` et règles métier ; renvoient des modèles Pydantic de `app/schemas.py`. `repositories/common.py::fetch_or_404` factorise « une ligne ou 404 ».
- `app/schema.sql` : tables + vues. `init_db` l'exécute au démarrage (idempotent, `CREATE ... IF NOT EXISTS`) : il n'y a pas de migrations, une modification de table existante demande de recréer la base.

Points transverses :

- **Connexion** : `get_conn` ouvre une connexion par requête, commit en fin de requête, rollback sur exception. Le chemin vient de `DOSSARD_DB`, sinon `data/dossard.db`.
- **Erreurs** : lever `ApiError` / `NotFoundError` / `ConflictError` (`app/errors.py`) avec un `code` explicite ; le handler global de `app/main.py` les sérialise en `{"error": {"code", "message"}}`. Les codes sont listés dans `docs/api.md`.
- **Logique pure** : `app/categories.py` (catégorie d'âge = année de saison − année de naissance) et `app/ranking.py` (temps croissants, distances/points décroissants) n'accèdent pas à la base.
- **Vues publiques** : `v_public_athletes` et `v_public_results` n'exposent que des colonnes non sensibles (année de naissance seule, inscriptions confirmées seulement). Le serveur MCP `scripts/mcp_dossard.py` (stdlib seule, lecture seule, ne lit que ces deux vues) en dépend : ne pas y ajouter de colonnes personnelles.
- **Scripts** (`scripts/`) : `seed.py`, `classement_html.py` (appelle l'API via `TestClient`, sans serveur), `mcp_dossard.py`, `recepteur_hooks.py`. `scripts/legacy/` est du code historique, exclu de ruff.

## Règles

- **Tests verts avant tout commit** : `pytest`.
- **Après toute modification Python** : `ruff check . && ruff format .` est obligatoire.
- **Erreurs** : format `{"error": {"code", "message"}}`, toujours via `app/errors.py` (`ApiError`, `NotFoundError`, `ConflictError`), **jamais `HTTPException`**.
- **Tests** :
  - un fichier de test par router ;
  - réutiliser les fixtures de `tests/conftest.py` : `client`, `make_competition`, `make_event`, `make_athlete`, `make_registration` (pas de SQL direct) ;
  - toujours tester les cas d'erreur (404, 409, 422) ;
  - chaque test a sa base temporaire (`db_path` via `DOSSARD_DB`) : ne jamais toucher `data/dossard.db`.
- **Route ajoutée ou modifiée** : une ligne dans `docs/api.md` **et** une entrée en tête de `CHANGELOG.md`, section « Non publié » (créer le fichier s'il n'existe pas).
- **`scripts/legacy/`** : lecture autorisée, aucune modification ni suppression sans demande explicite.
- **Dépendances** : pas de nouvelle dépendance sans demander.
- Ne jamais lire ni afficher .env : il contient des secrets.

## Conventions

- Style des nouveaux endpoints : modèle de `routers/registrations.py` (noms en snake_case, annotations de type complètes — ruff impose `ANN`, `from __future__ import annotations`). `routers/results.py` contient des restes à ne pas imiter : fonctions en camelCase (`getRanking`, `exportCsv`), `HTTPException` avec `detail`, réponse `dict` non typée.
- Les données d'exemple et de test sont synthétiques : aucune donnée personnelle réelle.
- `CLAUDE.local.md` et `.claude/settings.local.json` sont personnels et ignorés par Git.
