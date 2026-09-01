"""Routes de la page d'accueil et de la carte."""

from flask import Blueprint, render_template
from sqlalchemy import func

from config import Config
from models.db import Session
from models.dimensions import Departement, ProfessionSante, Region


bp_accueil = Blueprint("accueil", __name__)


def _libelle_region(region):
    """Retourne un libelle de region corrige pour l'affichage."""
    corrections = {
        "FRANCE": "France",
        "Ile-de-France": "Île-de-France",
    }
    return corrections.get(region.libelle, region.libelle)


def _preparer_regions(regions):
    """Retire l'agregat France puis trie les regions affichees."""
    regions = [region for region in regions if region.code != "99"]
    for region in regions:
        region.display_libelle = _libelle_region(region)
    return sorted(regions, key=lambda region: region.display_libelle)


@bp_accueil.route("/")
def index():
    """Affiche le formulaire, la carte et ses donnees de reference."""
    session = Session()
    try:
        regions = _preparer_regions(session.query(Region).order_by(Region.libelle).all())
        professions = (
            session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        )
        departements = session.query(Departement).order_by(Departement.code).all()
        region_stats = {
            row.Region.code: {
                "id": row.Region.id,
                "code": row.Region.code,
                "libelle": _libelle_region(row.Region),
                "departements": row.departements_count,
            }
            for row in (
                session.query(Region, func.count(Departement.id).label("departements_count"))
                .outerjoin(Departement)
                .group_by(Region.id)
                .all()
            )
        }
        departement_stats = {
            dept.code: {
                "id": dept.id,
                "code": dept.code,
                "libelle": dept.libelle,
                "region_id": dept.region_id,
                "region_code": dept.region.code,
                "region_libelle": _libelle_region(dept.region),
            }
            for dept in departements
        }
        return render_template(
            "accueil.html",
            regions=regions,
            professions=professions,
            region_stats=region_stats,
            departement_stats=departement_stats,
            annees=Config.ANNEES,
        )
    finally:
        session.close()
