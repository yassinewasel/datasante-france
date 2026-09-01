"""Genere une base SQLite deterministe avec des donnees synthetiques."""

import argparse
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import BASE_DIR
from models.dimensions import (
    Base, Departement, EffectifDemo, HonoraireDemo, PathologieDemo,
    PrescriptionDemo, ProfessionSante, Region, Sexe, TrancheAge,
    TypeExercice, TypeHonoraire, TypePrescription, TypeSecteur,
)


DEFAULT_PATH = BASE_DIR / "data" / "datasante_demo.db"


def initialize_demo_database(path=DEFAULT_PATH, force=False):
    """Cree exclusivement la base de demonstration demandee."""
    path = Path(path).resolve()
    if path.exists():
        if not force:
            raise FileExistsError(f"La base existe deja : {path}. Utilisez --force pour la recreer.")
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        _seed(session)
        session.commit()
    finally:
        session.close()
        engine.dispose()
    return path


def _seed(session):
    regions = [Region(id=1, code="11", libelle="Ile-de-France"), Region(id=2, code="84", libelle="Auvergne-Rhone-Alpes")]
    departments = [
        Departement(id=1, code="75", libelle="Paris", region_id=1),
        Departement(id=2, code="78", libelle="Yvelines", region_id=1),
        Departement(id=3, code="69", libelle="Rhone", region_id=2),
        Departement(id=4, code="38", libelle="Isere", region_id=2),
    ]
    professions = [ProfessionSante(id=1, libelle="Medecin generaliste"), ProfessionSante(id=2, libelle="Infirmier")]
    prescriptions = [TypePrescription(id=1, libelle="Medicaments"), TypePrescription(id=2, libelle="Biologie")]
    session.add_all(regions + departments + professions + prescriptions)
    session.add_all([Sexe(id=1, libelle="Femmes"), Sexe(id=2, libelle="Hommes")])
    session.add_all([TrancheAge(id=1, libelle="Tout age"), TrancheAge(id=2, libelle="Moins de 40 ans"), TrancheAge(id=3, libelle="40 ans et plus")])
    session.add_all([TypeExercice(id=1, libelle="Liberal"), TypeExercice(id=2, libelle="Salarie")])
    session.add(TypeHonoraire(id=1, niveau_1="Honoraires", niveau_2="Synthese"))
    session.add_all([TypeSecteur(id=1, code="S1", libelle="Secteur 1"), TypeSecteur(id=2, code="S2", libelle="Secteur 2")])

    for profession_index, profession in enumerate(professions, start=1):
        for region in regions:
            region_departments = [d for d in departments if d.region_id == region.id]
            territories = [("999", 3)] + [(d.code, index + 1) for index, d in enumerate(region_departments)]
            for dept_code, territory_factor in territories:
                for year in range(2019, 2024):
                    base = 700 + profession_index * 180 + region.id * 90 + territory_factor * 45 + (year - 2019) * 32
                    session.add(EffectifDemo(profession=profession.libelle, region_code=region.code, departement_code=dept_code, annee=year, sexe="tout sexe", age="Tout age", effectif=base, densite=round(base / 18.0, 2)))
                    for sexe, ratio in (("femmes", .57), ("hommes", .43)):
                        session.add(EffectifDemo(profession=profession.libelle, region_code=region.code, departement_code=dept_code, annee=year, sexe=sexe, age="Tout age", effectif=round(base * ratio), densite=0))
                    for age, ratio in (("Moins de 40 ans", .46), ("40 ans et plus", .54)):
                        session.add(EffectifDemo(profession=profession.libelle, region_code=region.code, departement_code=dept_code, annee=year, sexe="tout sexe", age=age, effectif=round(base * ratio), densite=0))
                    session.add(HonoraireDemo(profession=profession.libelle, region_code=region.code, departement_code=dept_code, annee=year, sans_depassement_total=base * 4200, sans_depassement_moyen=4200 + year - 2019, depassement_total=base * 310, depassement_moyen=310 + year - 2019))
                    for poste_index, poste in enumerate(prescriptions, start=1):
                        session.add(PrescriptionDemo(profession=profession.libelle, poste=poste.libelle, region_code=region.code, departement_code=dept_code, annee=year, montant_total=base * (500 + poste_index * 120), montant_moyen=500 + poste_index * 120))
                if profession_index == 1:
                    for pathology_index, pathology in enumerate(("Diabete", "Maladies respiratoires"), start=1):
                        for year in range(2019, 2024):
                            population = 120000 + region.id * 20000 + territory_factor * 5000
                            session.add(PathologieDemo(pathologie=pathology, region_code=region.code, departement_code=dept_code, annee=year, personnes=round(population * (.035 + pathology_index * .008 + (year - 2019) * .001)), population=population))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recree uniquement la base SQLite de demonstration.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args()
    path = initialize_demo_database(args.path, args.force)
    print(f"Base de demonstration creee : {path}")


if __name__ == "__main__":
    main()
