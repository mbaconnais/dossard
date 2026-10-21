"""Hook PostToolUse : formate avec ruff le code Python que Claude vient d'écrire.

- Write/Edit : formate le seul fichier `.py` modifié (`file_path`).
- Bash/PowerShell : on ignore quels fichiers la commande a touchés, donc on formate
  les dossiers de code du projet (`scripts/legacy/` est exclu par la config ruff).
"""

from __future__ import annotations

import json
import subprocess
import sys

DOSSIERS = ["app", "tests", "scripts"]

entree = json.load(sys.stdin)
chemin = str(entree.get("tool_input", {}).get("file_path", ""))
if chemin:
    cibles = [chemin] if chemin.endswith(".py") else []
else:
    cibles = DOSSIERS
if cibles:
    subprocess.run([sys.executable, "-m", "ruff", "format", "--quiet", *cibles], check=False)
