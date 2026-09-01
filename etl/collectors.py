"""Collecteurs idempotents des neuf tables de dimensions."""

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


DEMOGRAPHY_DATASET = "demographie-effectifs-et-les-densites"
HONORAIRES_SELECT = (
    "type_honoraires_niveau_1,type_honoraires_niveau_2,"
    "type_honoraires_niveau_3"
)
SECTORS = (
    ("S1", "Secteur 1"),
    ("S2", "Secteur 2"),
    ("S2_OPTAM", "Secteur 2 OPTAM"),
    ("NC", "Non conventionne"),
)


def _add_label(session, model, label):
    if label and not session.query(model).filter_by(libelle=label).first():
        session.add(model(libelle=label))


def collect_geography_and_professions(session, client):
    """Charge regions, departements, professions, ages et sexes."""
    regions = client.collect_all(
        DEMOGRAPHY_DATASET,
        select="region,libelle_region",
        group_by="region,libelle_region",
    )
    for item in regions:
        code, label = item.get("region"), item.get("libelle_region")
        if code and label and not session.query(Region).filter_by(code=code).first():
            session.add(Region(code=code, libelle=label))
    session.flush()

    region_ids = {region.code: region.id for region in session.query(Region).all()}
    departments = client.collect_all(
        DEMOGRAPHY_DATASET,
        select="departement,libelle_departement,region",
        where="departement != '999'",
        group_by="departement,libelle_departement,region",
    )
    for item in departments:
        code = item.get("departement")
        region_id = region_ids.get(item.get("region"))
        if code and item.get("libelle_departement") and region_id:
            if not session.query(Departement).filter_by(code=code).first():
                session.add(
                    Departement(
                        code=code,
                        libelle=item["libelle_departement"],
                        region_id=region_id,
                    )
                )

    dimensions = (
        (ProfessionSante, "profession_sante"),
        (TrancheAge, "libelle_classe_age"),
        (Sexe, "libelle_sexe"),
    )
    for model, field in dimensions:
        for item in client.collect_all(
            DEMOGRAPHY_DATASET, select=field, group_by=field
        ):
            _add_label(session, model, item.get(field))
    session.commit()


def collect_activity(session, client):
    """Charge les types d'exercice et le referentiel des secteurs."""
    field = "libelle_type_exercice_liberal"
    for item in client.collect_all(
        "demographie-exercices-liberaux", select=field, group_by=field
    ):
        _add_label(session, TypeExercice, item.get(field))
    for code, label in SECTORS:
        if not session.query(TypeSecteur).filter_by(code=code).first():
            session.add(TypeSecteur(code=code, libelle=label))
    session.commit()


def collect_financial(session, client):
    """Charge les hierarchies d'honoraires et les postes de prescription."""
    for item in client.collect_all(
        "honoraires-detailles",
        select=HONORAIRES_SELECT,
        group_by=HONORAIRES_SELECT,
    ):
        values = {
            "niveau_1": item.get("type_honoraires_niveau_1") or "",
            "niveau_2": item.get("type_honoraires_niveau_2") or None,
            "niveau_3": item.get("type_honoraires_niveau_3") or None,
        }
        if values["niveau_1"] and not session.query(TypeHonoraire).filter_by(
            **values
        ).first():
            session.add(TypeHonoraire(**values))

    field = "libelle_poste_prescription"
    for item in client.collect_all(
        "prescriptions", select=field, group_by=field
    ):
        _add_label(session, TypePrescription, item.get(field))
    session.commit()


def collect_all_dimensions(session, client):
    """Execute les trois groupes de collecteurs dans l'ordre des dependances."""
    collect_geography_and_professions(session, client)
    collect_activity(session, client)
    collect_financial(session, client)

