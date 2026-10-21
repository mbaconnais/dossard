# Dossard — référence API

Toute évolution de l'API doit être reportée ici (règle du projet).

## Format des erreurs

Toutes les erreurs métier renvoient :

```json
{ "error": { "code": "not_found", "message": "Compétition 42 introuvable" } }
```

| Code | Statut | Cas |
|---|---|---|
| `bad_request` | 400 | requête invalide (code par défaut) |
| `invalid_csv` | 400 | CSV d'import illisible (encodage) ou colonnes manquantes |
| `not_found` | 404 | ressource introuvable |
| `conflict` | 409 | doublon (licence, inscription déjà active) |
| `invalid_transition` | 409 | changement de statut non permis |
| `registrations_closed` | 409 | compétition non ouverte aux inscriptions |
| `category_mismatch` | 409 | catégorie de l'athlète différente de celle de l'épreuve |
| `medical_certificate_invalid` | 409 | certificat absent ou expiré à la date de la compétition |
| `results_not_allowed` | 409 | résultat sur une inscription non confirmée ou une compétition non close |

Les erreurs de validation (422) gardent le format FastAPI par défaut.

## Endpoints

| Méthode | Route | Description | Codes |
|---|---|---|---|
| GET | `/competitions` | Liste les compétitions triées par date, filtres optionnels `?status=draft\|open\|closed\|finished` et `?q=` (texte contenu dans le nom) | 200, 422 |
| POST | `/competitions` | Crée une compétition (`name`, `date` obligatoires, `venue` optionnel), au statut `draft` | 201, 422 |
| GET | `/competitions/{competition_id}` | Détail d'une compétition avec ses épreuves | 200, 404 |
| PATCH | `/competitions/{competition_id}` | Modifie `name`, `venue`, `date` et/ou `status` | 200, 404, 409, 422 |
| POST | `/competitions/{competition_id}/events` | Ajoute une épreuve (`name`, `unit`, `category` optionnelle) | 201, 404, 422 |
| GET | `/athletes` | Liste les athlètes triés par nom, filtre optionnel `?club=` (égalité exacte), pagination `?limit=` (1–100, défaut 50) et `?offset=` (≥ 0, défaut 0) appliquées après le filtre ; réponse = liste simple | 200, 422 |
| GET | `/athletes/{athlete_id}` | Renvoie un athlète avec sa `category` pour la saison en cours | 200, 404, 422 |
| POST | `/athletes` | Crée un athlète ; la réponse ajoute sa `category` pour la saison en cours | 201, 409, 422 |
| POST | `/athletes/import` | Importe un CSV brut (`Content-Type: text/csv`, séparateur `;`, dates `jj/mm/aaaa`) ; renvoie `created`, `skipped` (licence déjà enregistrée) et `errors` (`line`, `message`) sans bloquer les lignes valides | 200, 400 |
| POST | `/events/{event_id}/registrations` | Inscrit un athlète (`athlete_id`) à une épreuve et lui attribue un dossard | 201, 404, 409, 422 |
| PATCH | `/registrations/{registration_id}` | Change le `status` d'une inscription | 200, 404, 409, 422 |
| PUT | `/registrations/{registration_id}/result` | Enregistre ou remplace la `performance` d'une inscription | 200, 404, 409, 422 |
| GET | `/events/{event_id}/ranking` | Classement de l'épreuve : liste d'entrées `rank`, `bib`, `athlete_id`, `last_name`, `first_name`, `club`, `performance` | 200, 404 |
| GET | `/competitions/{competition_id}/results.csv` | Export CSV des résultats de la compétition | 200, 404 |

## Règles métier

- **R1** On ne s'inscrit qu'à une épreuve d'une compétition `open`.
- **R2** Un athlète n'a qu'une inscription non annulée par épreuve.
- **R3** Si l'épreuve a une catégorie, celle de l'athlète pour la saison de la compétition doit être la même.
- **R4** Le certificat médical doit exister et être valide à la date de la compétition.
- **R5** Le dossard vaut le plus grand dossard de la compétition plus un, annulations comprises : il n'est jamais réattribué.
- **R6** Un résultat ne s'enregistre que sur une inscription `confirmed` d'une compétition `closed`.
- **R7** Le numéro de licence (`DOS-` suivi de 6 chiffres) est unique.
- **R8** Le classement ne contient que les inscriptions `confirmed` ayant un résultat.

Transitions : une compétition passe de `draft` à `open`, puis `closed`, puis `finished`. Une inscription passe de `pending` à `confirmed` ou `cancelled`, et de `confirmed` à `cancelled`. Toute autre transition renvoie 409 `invalid_transition`.

## Catégories d'âge

L'âge de référence est l'âge atteint au 31/12 de la saison (année de la compétition − année de naissance).

| Catégorie | Âge de référence |
|---|---|
| `U16` | 15 ans et moins |
| `U18` | 16-17 |
| `U20` | 18-19 |
| `SENIOR` | 20-34 |
| `MASTER` | 35 et plus |
