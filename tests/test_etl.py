from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from etl.collectors import collect_all_dimensions
from etl.verify import dimension_counts, orphan_department_codes
from models.dimensions import Base, Region


class FakeClient:
    def collect_all(self, dataset, select=None, where=None, group_by=None):
        responses = {
            "region,libelle_region": [
                {"region": "11", "libelle_region": "Ile-de-France"}
            ],
            "departement,libelle_departement,region": [
                {
                    "departement": "75",
                    "libelle_departement": "Paris",
                    "region": "11",
                }
            ],
            "profession_sante": [{"profession_sante": "Medecin generaliste"}],
            "libelle_classe_age": [{"libelle_classe_age": "40 a 49 ans"}],
            "libelle_sexe": [{"libelle_sexe": "Femmes"}],
            "libelle_type_exercice_liberal": [
                {"libelle_type_exercice_liberal": "Cabinet individuel"}
            ],
            (
                "type_honoraires_niveau_1,type_honoraires_niveau_2,"
                "type_honoraires_niveau_3"
            ): [
                {
                    "type_honoraires_niveau_1": "Honoraires",
                    "type_honoraires_niveau_2": "Actes",
                    "type_honoraires_niveau_3": None,
                }
            ],
            "libelle_poste_prescription": [
                {"libelle_poste_prescription": "Pharmacie"}
            ],
        }
        return responses[select]


def test_collectors_are_idempotent_and_keep_geography_consistent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Region(code="84", libelle="Auvergne-Rhone-Alpes"))
    session.commit()

    collect_all_dimensions(session, FakeClient())
    first_counts = dimension_counts(session)
    collect_all_dimensions(session, FakeClient())

    assert dimension_counts(session) == first_counts
    assert first_counts == {
        "regions": 2,
        "departements": 1,
        "professions": 1,
        "tranches_age": 1,
        "sexes": 1,
        "types_exercice": 1,
        "secteurs": 4,
        "types_honoraires": 1,
        "types_prescription": 1,
    }
    assert orphan_department_codes(session) == []
    assert session.query(Region).filter_by(code="84").one()

