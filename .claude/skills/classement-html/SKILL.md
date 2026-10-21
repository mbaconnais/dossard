---
name: classement-html
description: Produit la page HTML (un fichier .html) du classement d'une épreuve de dossard. À utiliser quand on demande une page, un fichier HTML ou une version imprimable/partageable du classement ou des résultats d'une épreuve.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py *)
---

# Classement HTML d'une épreuve

Le script `scripts/classement_html.py` de cette skill interroge `GET /events/{event_id}/ranking` et écrit la page HTML : elle reflète exactement ce que renvoie l'API.

## Instructions

1. **Identifiant de l'épreuve** : s'il n'est pas donné, le chercher par le nom dans `data/dossard.db`, en lecture seule :

   ```bash
   sqlite3 -readonly data/dossard.db "SELECT id, name FROM events WHERE name LIKE '%<mot>%'"
   ```

   Si plusieurs épreuves correspondent, ou aucune, demander à l'utilisateur laquelle choisir plutôt que de deviner.

2. **Génération** : depuis la racine du dépôt, venv activé :

   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py <event_id>
   ```

3. **Ne pas écrire de HTML soi-même** : la page vient uniquement du script. S'il échoue (base absente, épreuve introuvable, classement indisponible), rapporter son message tel quel sans contourner.

4. **Réponse** : donner le chemin du fichier produit (`classement-<event_id>.html`, écrit dans le répertoire courant) et le nombre d'athlètes classés affiché par le script.
