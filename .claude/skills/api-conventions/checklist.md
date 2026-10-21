# Checklist des routes

- [ ] Erreurs métier par `app/errors.py` (`NotFoundError`, `ConflictError`), jamais `HTTPException`.
- [ ] Paramètres de chemin et fonctions en snake_case (`event_id`, `get_ranking`).
- [ ] Réponse de liste : la liste nue, sans enveloppe (`{"data", "count"}` interdit), avec `response_model`.
- [ ] Chaque décorateur de route porte un `summary=` en français, à l'infinitif (« Lister le classement d'une épreuve »).
- [ ] Contrat modifié : tests adaptés, `docs/api.md` et `CHANGELOG.md` à jour.
