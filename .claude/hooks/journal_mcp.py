"""Hook PreToolUse : ajoute chaque appel d'outil MCP au journal data/journal-mcp.log."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

entree = json.load(sys.stdin)
ligne = {
    "date": datetime.now(UTC).isoformat(timespec="seconds"),
    "outil": entree.get("tool_name"),
    "arguments": entree.get("tool_input"),
}
journal = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "data" / "journal-mcp.log"
with journal.open("a", encoding="utf-8") as fichier:
    fichier.write(json.dumps(ligne, ensure_ascii=False) + "\n")
