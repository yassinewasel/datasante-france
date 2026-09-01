"""Service de donnees synthetiques stockees dans SQLite."""

from models.db import Session
from models.dimensions import EffectifDemo, HonoraireDemo, PathologieDemo, PrescriptionDemo


class DemoDataService:
    """Expose la meme interface que le client Data Ameli, sans reseau."""

    derniere_erreur = None

    @staticmethod
    def _territory(code):
        return code or "999"

    @staticmethod
    def _effectif_dict(row):
        return {"annee": row.annee, "effectif": row.effectif, "densite": row.densite}

    def get_effectifs(self, profession, departement_code, annee, sexe="tout sexe", age="Tout age"):
        session = Session()
        try:
            row = session.query(EffectifDemo).filter_by(profession=profession, departement_code=departement_code, annee=annee, sexe=sexe, age=age).first()
            return [self._effectif_dict(row)] if row else []
        finally:
            session.close()

    def get_evolution_effectifs(self, profession, departement_code, sexe="tout sexe", age="Tout age"):
        session = Session()
        try:
            rows = session.query(EffectifDemo).filter_by(profession=profession, departement_code=departement_code, sexe=sexe, age=age).order_by(EffectifDemo.annee).all()
            return [self._effectif_dict(row) for row in rows]
        finally:
            session.close()

    def get_effectifs_territoire(self, profession, region_code, departement_code, annee_debut, annee_fin):
        session = Session()
        try:
            rows = session.query(EffectifDemo).filter(
                EffectifDemo.profession == profession,
                EffectifDemo.region_code == region_code,
                EffectifDemo.departement_code == self._territory(departement_code),
                EffectifDemo.annee.between(annee_debut, annee_fin),
                EffectifDemo.sexe == "tout sexe",
                EffectifDemo.age == "Tout age",
            ).order_by(EffectifDemo.annee).all()
            return [self._effectif_dict(row) for row in rows]
        finally:
            session.close()

    def get_repartitions_effectifs(self, profession, region_code, departement_code, annee):
        session = Session()
        try:
            base = [
                EffectifDemo.profession == profession,
                EffectifDemo.region_code == region_code,
                EffectifDemo.departement_code == self._territory(departement_code),
                EffectifDemo.annee == annee,
            ]
            sexes = session.query(EffectifDemo).filter(*base, EffectifDemo.age == "Tout age", EffectifDemo.sexe != "tout sexe").all()
            ages = session.query(EffectifDemo).filter(*base, EffectifDemo.sexe == "tout sexe", EffectifDemo.age != "Tout age").all()
            return {
                "sexes": [{"libelle_sexe": row.sexe, "effectif": row.effectif} for row in sexes],
                "ages": [{"libelle_classe_age": row.age, "effectif": row.effectif} for row in ages],
            }
        finally:
            session.close()

    def get_honoraires(self, profession, region_code, departement_code, annee_debut, annee_fin):
        session = Session()
        try:
            rows = session.query(HonoraireDemo).filter(
                HonoraireDemo.profession == profession,
                HonoraireDemo.region_code == region_code,
                HonoraireDemo.departement_code == self._territory(departement_code),
                HonoraireDemo.annee.between(annee_debut, annee_fin),
            ).order_by(HonoraireDemo.annee).all()
            return [{"annee": row.annee, "hono_sans_depassement_totaux_integer": row.sans_depassement_total, "hono_sans_depassement_moyens_integer": row.sans_depassement_moyen, "depassements_totaux_integer": row.depassement_total, "depassements_moyens_integer": row.depassement_moyen} for row in rows]
        finally:
            session.close()

    def get_prescriptions(self, profession, poste, region_code, departement_code, annee_debut, annee_fin):
        session = Session()
        try:
            rows = session.query(PrescriptionDemo).filter(
                PrescriptionDemo.profession == profession,
                PrescriptionDemo.poste == poste,
                PrescriptionDemo.region_code == region_code,
                PrescriptionDemo.departement_code == self._territory(departement_code),
                PrescriptionDemo.annee.between(annee_debut, annee_fin),
            ).order_by(PrescriptionDemo.annee).all()
            return [{"annee": row.annee, "libelle_poste_prescription": row.poste, "montant_total_prescription_integer": row.montant_total, "montant_moyen_prescription_integer": row.montant_moyen} for row in rows]
        finally:
            session.close()

    def get_pathologies(self):
        session = Session()
        try:
            return [row[0] for row in session.query(PathologieDemo.pathologie).distinct().order_by(PathologieDemo.pathologie).all()]
        finally:
            session.close()

    def get_pathologie_effectifs(self, pathologie, region_code, departement_code, annee_debut, annee_fin):
        session = Session()
        try:
            rows = session.query(PathologieDemo).filter(
                PathologieDemo.pathologie == pathologie,
                PathologieDemo.region_code == region_code,
                PathologieDemo.departement_code == self._territory(departement_code),
                PathologieDemo.annee.between(annee_debut, annee_fin),
            ).order_by(PathologieDemo.annee).all()
            return [{"annee": row.annee, "ntop": row.personnes, "npop": row.population} for row in rows]
        finally:
            session.close()
