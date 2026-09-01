"""Calculs réutilisables pour les séries temporelles de santé."""


def _nombre(valeur):
    """Convertit une valeur en nombre ou renvoie None."""
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def analyser_evolution(evolution, annee_selectionnee):
    """Calcule les reperes utiles d'une evolution annuelle."""
    lignes = [
        {
            "annee": str(ligne["annee"])[:4],
            "effectif": _nombre(ligne.get("effectif")),
            "densite": _nombre(ligne.get("densite")),
        }
        for ligne in evolution
        if ligne.get("annee") is not None
    ]
    lignes.sort(key=lambda ligne: ligne["annee"])
    selection = next(
        (ligne for ligne in lignes if ligne["annee"] == str(annee_selectionnee)),
        lignes[-1] if lignes else None,
    )
    precedent = lignes[lignes.index(selection) - 1] if selection and lignes.index(selection) else None
    effectifs = [ligne["effectif"] for ligne in lignes if ligne["effectif"] is not None]
    densites = [ligne["densite"] for ligne in lignes if ligne["densite"] is not None]
    variation = None
    variation_pct = None
    if selection and precedent and selection["effectif"] is not None and precedent["effectif"] is not None:
        variation = selection["effectif"] - precedent["effectif"]
        if precedent["effectif"]:
            variation_pct = (variation / precedent["effectif"]) * 100

    return {
        "selection": selection,
        "precedent": precedent,
        "variation": variation,
        "variation_pct": variation_pct,
        "moyenne_effectif": sum(effectifs) / len(effectifs) if effectifs else None,
        "moyenne_densite": sum(densites) / len(densites) if densites else None,
        "max": max(lignes, key=lambda ligne: ligne["effectif"] or float("-inf"), default=None),
        "min": min(lignes, key=lambda ligne: ligne["effectif"] or float("inf"), default=None),
        "points": len(lignes),
    }
