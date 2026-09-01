"""Controles simples apres chargement des dimensions."""

from models.dimensions import (
    Departement,
    ProfessionSante,
    Region,
    Sexe,
    TrancheAge,
    TypeExercice,
    TypeHonoraire,
    TypePrescription,
    TypeSecteur,
)


DIMENSIONS = {
    "regions": Region,
    "departements": Departement,
    "professions": ProfessionSante,
    "tranches_age": TrancheAge,
    "sexes": Sexe,
    "types_exercice": TypeExercice,
    "secteurs": TypeSecteur,
    "types_honoraires": TypeHonoraire,
    "types_prescription": TypePrescription,
}


def dimension_counts(session):
    return {name: session.query(model).count() for name, model in DIMENSIONS.items()}


def orphan_department_codes(session):
    """Retourne les departements dont la region n'existe pas."""
    rows = (
        session.query(Departement.code)
        .outerjoin(Region, Departement.region_id == Region.id)
        .filter(Region.id.is_(None))
        .all()
    )
    return [code for (code,) in rows]

