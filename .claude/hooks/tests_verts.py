"""Hook Stop : Claude ne rend pas la main tant que pytest est rouge."""

from __future__ import annotations

import json
import subprocess
import sys

entree = json.load(sys.stdin)
if entree.get("stop_hook_active"):
    sys.exit(0)  # déjà relancé par ce hook : on le laisse s'arrêter, pas de boucle
res = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-x", "--no-header"],
    capture_output=True,
    text=True,
    check=False,
    cwd=entree.get("cwd"),
)
if res.returncode != 0:
    fin = "\n".join(res.stdout.strip().splitlines()[-15:])
    print(
        f"Hook tests_verts.py : pytest est rouge, corrige avant de t'arrêter.\n{fin}",
        file=sys.stderr,
    )
    sys.exit(2)
