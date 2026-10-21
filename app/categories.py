from __future__ import annotations

from datetime import date

from app.schemas import AgeCategory


def age_category(birth_date: date, on: date | None = None) -> AgeCategory:
    """Catégorie d'âge pour la saison qui contient `on` (aujourd'hui par défaut).

    L'âge de référence est l'année de la saison moins l'année de naissance,
    soit l'âge atteint au 31/12 de la saison.
    """
    season = (on or date.today()).year
    age = season - birth_date.year
    if age <= 15:
        return AgeCategory.U16
    if age <= 17:
        return AgeCategory.U18
    if age <= 19:
        return AgeCategory.U20
    if age <= 34:
        return AgeCategory.SENIOR
    return AgeCategory.MASTER


def est_junior(birth_date: date, on: date | None = None) -> bool:
    return age_category(birth_date, on=on) in (AgeCategory.U18, AgeCategory.U20)
