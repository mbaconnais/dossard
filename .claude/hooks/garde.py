#!/usr/bin/env python3
"""Hook PreToolUse : bloque quelques commandes shell destructrices.

Lit le JSON de Claude Code sur l'entrée standard. Pour les outils Bash et PowerShell,
refuse (code 2, message sur stderr) les commandes contenant :
  - rm -rf (options -rf, -fr, -r -f, --recursive --force, dans n'importe quel ordre) ;
  - git push --force ou -f ;
  - DROP TABLE / DROP VIEW (sans tenir compte de la casse).
Dans tous les autres cas, sort avec le code 0.
"""

from __future__ import annotations

import json
import re
import sys

OUTILS_SHELL = {"Bash", "PowerShell"}
SEPARATEURS = re.compile(r"[;&|\n]+")
DROP = re.compile(r"\bDROP\s+(TABLE|VIEW)\b", re.IGNORECASE)


def jetons(segment: str) -> list[str]:
    """Découpe un segment en mots, guillemets retirés (couvre `bash -c "rm -rf x"`)."""
    return [j.strip("\"'`()") for j in segment.split()]


def options_apres(
    mots: list[str], commande: str, sous_commande: str | None = None
) -> set[str] | None:
    """Options (`-x`, `--xxx`) suivant `commande` [+ `sous_commande`], ou None si absente."""
    for i, mot in enumerate(mots):
        if mot.rsplit("/", 1)[-1] != commande:
            continue
        reste = mots[i + 1 :]
        if sous_commande is not None:
            # `git -C dir push ...` : on cherche la sous-commande parmi les mots suivants.
            if sous_commande not in reste:
                continue
            reste = reste[reste.index(sous_commande) + 1 :]
        options: set[str] = set()
        for opt in reste:
            if opt == "--":
                break
            if opt.startswith("--"):
                options.add(opt)
            elif opt.startswith("-") and len(opt) > 1:
                options.update(f"-{c}" for c in opt[1:])
        return options
    return None


def raison_blocage(commande: str) -> str | None:
    if DROP.search(commande):
        return "DROP TABLE / DROP VIEW interdit"

    for segment in SEPARATEURS.split(commande):
        mots = jetons(segment)

        opts = options_apres(mots, "rm")
        if opts is not None:
            recursif = bool(opts & {"-r", "-R", "--recursive"})
            force = bool(opts & {"-f", "--force"})
            if recursif and force:
                return "rm -rf interdit"

        opts = options_apres(mots, "git", "push")
        if opts is not None and opts & {"--force", "-f"}:
            return "git push --force interdit"

    return None


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(donnees, dict) or donnees.get("tool_name") not in OUTILS_SHELL:
        return 0

    entree = donnees.get("tool_input")
    commande = entree.get("command") if isinstance(entree, dict) else None
    if not isinstance(commande, str):
        return 0

    raison = raison_blocage(commande)
    if raison:
        print(f"Bloqué par le hook garde.py : {raison}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
