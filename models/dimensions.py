"""Modeles SQLAlchemy des tables de dimensions de la SAE."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Region(Base):
    """Region administrative disponible dans les filtres."""
    __tablename__ = "region"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)
    libelle = Column(String(100), nullable=False)
    departements = relationship("Departement", back_populates="region")

    def to_dict(self):
        """Convertit la region en dictionnaire JSON."""
        return {"id": self.id, "code": self.code, "libelle": self.libelle}


class Departement(Base):
    """Departement rattache a une region."""
    __tablename__ = "departement"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)
    libelle = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("region.id"), nullable=False)
    region = relationship("Region", back_populates="departements")

    def to_dict(self):
        """Convertit le departement en dictionnaire JSON."""
        return {
            "id": self.id,
            "code": self.code,
            "libelle": self.libelle,
            "region_id": self.region_id,
        }


class ProfessionSante(Base):
    """Profession de sante du referentiel."""
    __tablename__ = "profession_sante"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False, unique=True)

    def to_dict(self):
        """Convertit la profession en dictionnaire JSON."""
        return {"id": self.id, "libelle": self.libelle}


class Sexe(Base):
    """Categorie de sexe disponible dans les donnees."""
    __tablename__ = "sexe"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False, unique=True)

    def to_dict(self):
        """Convertit la categorie en dictionnaire JSON."""
        return {"id": self.id, "libelle": self.libelle}


class TrancheAge(Base):
    """Tranche d'age disponible dans les donnees."""
    __tablename__ = "tranche_age"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(100), nullable=False, unique=True)

    def to_dict(self):
        """Convertit la tranche d'age en dictionnaire JSON."""
        return {"id": self.id, "libelle": self.libelle}


class TypeExercice(Base):
    """Type d'exercice professionnel du referentiel."""
    __tablename__ = "type_exercice"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False, unique=True)

    def to_dict(self):
        """Convertit le type d'exercice en dictionnaire JSON."""
        return {"id": self.id, "libelle": self.libelle}


class TypeHonoraire(Base):
    """Categorie hierarchique d'honoraires."""
    __tablename__ = "type_honoraire"

    id = Column(Integer, primary_key=True)
    niveau_1 = Column(String(80), nullable=False)
    niveau_2 = Column(String(80))
    niveau_3 = Column(String(80))

    def to_dict(self):
        """Convertit la categorie en dictionnaire JSON."""
        return {
            "id": self.id,
            "niveau_1": self.niveau_1,
            "niveau_2": self.niveau_2,
            "niveau_3": self.niveau_3,
        }

    @property
    def libelle(self):
        """Assemble les niveaux renseignes en un libelle lisible."""
        niveaux = [self.niveau_1, self.niveau_2, self.niveau_3]
        return " - ".join(n for n in niveaux if n)


class TypePrescription(Base):
    """Poste de prescription du referentiel."""
    __tablename__ = "type_prescription"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False, unique=True)

    def to_dict(self):
        """Convertit le poste en dictionnaire JSON."""
        return {"id": self.id, "libelle": self.libelle}


class TypeSecteur(Base):
    """Secteur d'activite du referentiel."""
    __tablename__ = "type_secteur"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    libelle = Column(String(200), nullable=False)

    def to_dict(self):
        """Convertit le secteur en dictionnaire JSON."""
        return {"id": self.id, "code": self.code, "libelle": self.libelle}


class EffectifDemo(Base):
    """Mesure synthetique d'effectif utilisee uniquement en mode demo."""
    __tablename__ = "effectif_demo"
    __table_args__ = (UniqueConstraint("profession", "region_code", "departement_code", "annee", "sexe", "age"),)

    id = Column(Integer, primary_key=True)
    profession = Column(String(200), nullable=False)
    region_code = Column(String(10), nullable=False)
    departement_code = Column(String(10), nullable=False, default="999")
    annee = Column(Integer, nullable=False)
    sexe = Column(String(50), nullable=False, default="tout sexe")
    age = Column(String(100), nullable=False, default="Tout age")
    effectif = Column(Integer, nullable=False)
    densite = Column(Float, nullable=False, default=0)


class HonoraireDemo(Base):
    __tablename__ = "honoraire_demo"
    id = Column(Integer, primary_key=True)
    profession = Column(String(200), nullable=False)
    region_code = Column(String(10), nullable=False)
    departement_code = Column(String(10), nullable=False, default="999")
    annee = Column(Integer, nullable=False)
    sans_depassement_total = Column(Integer, nullable=False)
    sans_depassement_moyen = Column(Integer, nullable=False)
    depassement_total = Column(Integer, nullable=False)
    depassement_moyen = Column(Integer, nullable=False)


class PrescriptionDemo(Base):
    __tablename__ = "prescription_demo"
    id = Column(Integer, primary_key=True)
    profession = Column(String(200), nullable=False)
    poste = Column(String(200), nullable=False)
    region_code = Column(String(10), nullable=False)
    departement_code = Column(String(10), nullable=False, default="999")
    annee = Column(Integer, nullable=False)
    montant_total = Column(Integer, nullable=False)
    montant_moyen = Column(Integer, nullable=False)


class PathologieDemo(Base):
    __tablename__ = "pathologie_demo"
    id = Column(Integer, primary_key=True)
    pathologie = Column(String(200), nullable=False)
    region_code = Column(String(10), nullable=False)
    departement_code = Column(String(10), nullable=False, default="999")
    annee = Column(Integer, nullable=False)
    personnes = Column(Integer, nullable=False)
    population = Column(Integer, nullable=False)
