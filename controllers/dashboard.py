"""Routes des pages d'analyse et de comparaison."""

from flask import Blueprint, render_template
from sqlalchemy import func

from config import Config
from models.db import Session
from models.dimensions import (
    Departement,
    ProfessionSante,
    Region,
    TrancheAge,
    TypeExercice,
    TypeHonoraire,
    TypePrescription,
)
from services.ameli_api import create_data_service


bp_dashboard = Blueprint("dashboard", __name__)
api_ameli = create_data_service()


def _libelle_region(region):
    """Retourne un nom de region adapte a l'interface."""
    corrections = {
        "FRANCE": "France",
        "Ile-de-France": "Île-de-France",
    }
    return corrections.get(region.libelle, region.libelle)


def _libelle_age(age):
    """Uniformise un libelle de tranche d'age."""
    corrections = {
        "âge inconnu": "Âge inconnu",
        "moins de 25 ans": "Moins de 25 ans",
    }
    if age.libelle in corrections:
        return corrections[age.libelle]
    if age.libelle.startswith("de "):
        return "De " + age.libelle[3:]
    return age.libelle


def _preparer_regions(regions):
    """Prepare et trie les regions proposees dans les filtres."""
    regions = [region for region in regions if region.code != "99"]
    for region in regions:
        region.display_libelle = _libelle_region(region)
    return sorted(regions, key=lambda region: region.display_libelle)


def _preparer_ages(ages):
    """Prepare et trie les tranches d'age pour les formulaires."""
    for age in ages:
        age.display_libelle = _libelle_age(age)
    return sorted(ages, key=lambda age: (age.libelle != "Tout âge", age.id))


def _group_professions(professions):
    """Compte les professions par grande famille."""
    groupes = {"Médecins": 0, "Dentistes": 0, "Auxiliaires": 0, "Autres": 0}
    for profession in professions:
        libelle = profession.libelle.lower()
        if "dentiste" in libelle:
            groupes["Dentistes"] += 1
        elif "médecin" in libelle or "chirurgien" in libelle:
            groupes["Médecins"] += 1
        elif any(mot in libelle for mot in ["infirmier", "kiné", "orthophon", "sage"]):
            groupes["Auxiliaires"] += 1
        else:
            groupes["Autres"] += 1
    return groupes


def _data():
    """Charge les referentiels communs aux tableaux de bord."""
    session = Session()
    try:
        regions = _preparer_regions(session.query(Region).order_by(Region.libelle).all())
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        exercices = session.query(TypeExercice).order_by(TypeExercice.id).all()
        honoraires = session.query(TypeHonoraire).order_by(TypeHonoraire.id).all()
        prescriptions = session.query(TypePrescription).order_by(TypePrescription.libelle).all()
        ages = _preparer_ages(session.query(TrancheAge).order_by(TrancheAge.id).all())
        departements = session.query(Departement).order_by(Departement.code).all()
        region_rows = (
            session.query(Region, func.count(Departement.id).label("departements_count"))
            .outerjoin(Departement)
            .group_by(Region.id)
            .order_by(Region.libelle)
            .all()
        )

        top_regions = sorted(
            [
                row
                for row in region_rows
                if row.Region.code not in {"01", "02", "03", "04", "06", "99"}
            ],
            key=lambda row: row.departements_count,
            reverse=True,
        )[:8]

        return {
            "regions": regions,
            "professions": professions,
            "exercices": exercices,
            "honoraires": honoraires,
            "prescriptions": prescriptions,
            "ages": ages,
            "departements": departements,
            "annees": Config.ANNEES,
            "region_rows": region_rows,
            "top_regions": top_regions,
            "profession_groups": _group_professions(professions),
            "kpis": {
                "regions": len(regions),
                "departements": len(departements),
                "professions": len(professions),
                "exercices": len(exercices),
                "honoraires": len(honoraires),
                "prescriptions": len(prescriptions),
            },
        }
    finally:
        session.close()


@bp_dashboard.route("/honoraires")
def honoraires():
    """Affiche la page d'analyse des honoraires."""
    return render_template("honoraires.html", **_data())


@bp_dashboard.route("/prescriptions")
def prescriptions():
    """Affiche la page d'analyse des prescriptions."""
    return render_template("prescriptions.html", **_data())


@bp_dashboard.route("/pathologies")
def pathologies():
    """Affiche la page d'analyse des pathologies."""
    donnees = _data()
    donnees["pathologies"] = api_ameli.get_pathologies()
    donnees["pathologies_erreur"] = api_ameli.derniere_erreur
    return render_template("pathologies.html", **donnees)


@bp_dashboard.route("/indicateurs")
def indicateurs():
    """Affiche les indicateurs clefs du projet."""
    return render_template("indicateurs.html", **_data())


@bp_dashboard.route("/comparaisons")
def comparaisons():
    """Affiche la page de comparaison de deux series."""
    return render_template("comparaisons.html", **_data())


@bp_dashboard.route("/a-propos")
def a_propos():
    """Affiche la presentation du projet."""
    return render_template("a_propos.html")
