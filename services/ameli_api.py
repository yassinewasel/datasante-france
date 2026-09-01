"""Client HTTP pour les jeux de donnees publics Data Ameli."""

import requests

from config import Config
from services.cache import avec_cache


class AmeliAPI:
    """Service d'accès à l'API publique data.ameli.fr."""

    BASE_URL = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets"
    EFFECTIFS_DATASET = "demographie-effectifs-et-les-densites"
    HONORAIRES_DATASET = "honoraires"
    PRESCRIPTIONS_DATASET = "prescriptions"
    PATHOLOGIES_DATASET = "effectifs"
    PATHOLOGIES_REFERENTIEL_DATASET = "referentiel-pathologies"

    def __init__(self, timeout=10):
        """Prepare une session HTTP reutilisable."""
        self._timeout = timeout
        self._session = requests.Session()
        self.derniere_erreur = None

    @avec_cache(duree_vie_seconde=300)
    def get_effectifs(
        self,
        profession,
        departement_code,
        annee,
        sexe="tout sexe",
        age="Tout âge",
    ):
        """Effectifs pour une profession, un département, une année et des filtres optionnels."""
        where = self._where_effectifs(
            profession,
            departement_code,
            annee=annee,
            sexe=sexe,
            age=age,
        )
        return self._requete(
            self.EFFECTIFS_DATASET,
            {
                "select": "annee,effectif,densite",
                "where": where,
                "order_by": "annee",
                "limit": 100,
            },
        )

    @avec_cache(duree_vie_seconde=600)
    def get_evolution_effectifs(
        self,
        profession,
        departement_code,
        sexe="tout sexe",
        age="Tout âge",
    ):
        """Effectifs sur toutes les années disponibles pour le graphique."""
        where = self._where_effectifs(
            profession,
            departement_code,
            sexe=sexe,
            age=age,
        )
        return self._requete(
            self.EFFECTIFS_DATASET,
            {
                "select": "annee,effectif,densite",
                "where": where,
                "order_by": "annee",
                "limit": 100,
            },
        )

    @avec_cache(duree_vie_seconde=600)
    def get_effectifs_territoire(
        self, profession, region_code, departement_code, annee_debut, annee_fin
    ):
        """Evolution des effectifs pour un département ou l'agrégat d'une région."""
        where = self._where_territoire(
            profession, region_code, departement_code, annee_debut, annee_fin
        )
        where += " AND libelle_classe_age='Tout âge' AND libelle_sexe='tout sexe'"
        return self._requete(
            self.EFFECTIFS_DATASET,
            {
                "select": "annee,effectif,densite",
                "where": where,
                "order_by": "annee",
                "limit": 100,
            },
        )

    @avec_cache(duree_vie_seconde=600)
    def get_repartitions_effectifs(
        self, profession, region_code, departement_code, annee
    ):
        """Répartitions sexe et âge pour la comparaison d'un territoire."""
        departement = departement_code or "999"
        base = [
            f"profession_sante={self._valeur_texte(profession)}",
            f"region={self._valeur_texte(region_code)}",
            f"departement={self._valeur_texte(departement)}",
            f"annee=date'{annee}'",
        ]
        sexes = self._requete(
            self.EFFECTIFS_DATASET,
            {
                "select": "libelle_sexe,effectif",
                "where": " AND ".join(base + ["libelle_classe_age='Tout âge'"]),
                "limit": 20,
            },
        )
        ages = self._requete(
            self.EFFECTIFS_DATASET,
            {
                "select": "libelle_classe_age,effectif",
                "where": " AND ".join(base + ["libelle_sexe='tout sexe'"]),
                "limit": 100,
            },
        )
        return {"sexes": sexes, "ages": ages}

    @avec_cache(duree_vie_seconde=600)
    def get_honoraires(
        self, profession, region_code, departement_code, annee_debut, annee_fin
    ):
        """Montants d'honoraires pour un territoire et une période."""
        return self._requete(
            self.HONORAIRES_DATASET,
            {
                "select": (
                    "annee,hono_sans_depassement_totaux_integer,"
                    "hono_sans_depassement_moyens_integer,"
                    "depassements_totaux_integer,depassements_moyens_integer"
                ),
                "where": self._where_territoire(
                    profession, region_code, departement_code, annee_debut, annee_fin
                ),
                "order_by": "annee",
                "limit": 100,
            },
        )

    @avec_cache(duree_vie_seconde=600)
    def get_prescriptions(
        self,
        profession,
        poste_prescription,
        region_code,
        departement_code,
        annee_debut,
        annee_fin,
    ):
        """Montants de prescriptions pour un poste, un territoire et une période."""
        where = self._where_territoire(
            profession, region_code, departement_code, annee_debut, annee_fin
        )
        where += f" AND libelle_poste_prescription={self._valeur_texte(poste_prescription)}"
        return self._requete(
            self.PRESCRIPTIONS_DATASET,
            {
                "select": (
                    "annee,libelle_poste_prescription,"
                    "montant_total_prescription_integer,montant_moyen_prescription_integer"
                ),
                "where": where,
                "order_by": "annee",
                "limit": 100,
            },
        )

    @avec_cache(duree_vie_seconde=3600)
    def get_pathologies(self):
        """Liste des pathologies disponibles dans le référentiel public."""
        rows = self._requete(
            self.PATHOLOGIES_REFERENTIEL_DATASET,
            {"select": "patho_niv2", "limit": 100},
        )
        return sorted({row["patho_niv2"] for row in rows if row.get("patho_niv2")})

    @avec_cache(duree_vie_seconde=600)
    def get_pathologie_effectifs(
        self, pathologie, region_code, departement_code, annee_debut, annee_fin
    ):
        """Effectifs de patients pour une pathologie, sans double compte âge/sexe."""
        departement = departement_code or "999"
        where = [
            f"patho_niv2={self._valeur_texte(pathologie)}",
            f"region={self._valeur_texte(region_code)}",
            f"dept={self._valeur_texte(departement)}",
            "cla_age_5='tsage'",
            "sexe='9'",
            f"annee >= date'{annee_debut}'",
            f"annee <= date'{annee_fin}'",
        ]
        return self._requete(
            self.PATHOLOGIES_DATASET,
            {
                "select": "annee,sum(ntop) as ntop,max(npop) as npop",
                "where": " AND ".join(where),
                "group_by": "annee",
                "order_by": "annee",
                "limit": 100,
            },
        )

    def _where_effectifs(self, profession, departement_code, annee=None, sexe="tout sexe", age="Tout âge"):
        """Construit le filtre API pour les effectifs departementaux."""
        filtres = [
            f"profession_sante={self._valeur_texte(profession)}",
            f"departement={self._valeur_texte(departement_code)}",
            f"libelle_classe_age={self._valeur_texte(age)}",
            f"libelle_sexe={self._valeur_texte(sexe)}",
        ]
        if annee:
            filtres.append(f"annee=date'{annee}'")
        return " AND ".join(filtres)

    def _where_territoire(
        self, profession, region_code, departement_code, annee_debut, annee_fin
    ):
        """Filtre commun aux jeux professionnels, avec agrégat régional si besoin."""
        departement = departement_code or "999"
        return " AND ".join(
            [
                f"profession_sante={self._valeur_texte(profession)}",
                f"region={self._valeur_texte(region_code)}",
                f"departement={self._valeur_texte(departement)}",
                f"annee >= date'{annee_debut}'",
                f"annee <= date'{annee_fin}'",
            ]
        )

    def _valeur_texte(self, valeur):
        """Echappe une valeur texte pour un filtre ODS."""
        return "'" + str(valeur).replace("\\", "\\\\").replace("'", "\\'") + "'"

    def _requete(self, dataset, params):
        """Effectue une requête GET et renvoie une liste de résultats."""
        url = f"{self.BASE_URL}/{dataset}/records"
        self.derniere_erreur = None

        try:
            reponse = self._session.get(url, params=params, timeout=self._timeout)
            reponse.raise_for_status()
            return reponse.json().get("results", [])
        except (requests.RequestException, ValueError) as erreur:
            self.derniere_erreur = str(erreur)
            print(f"[AmeliAPI] Erreur : {erreur}")
            return []


def create_data_service():
    """Selectionne explicitement SQLite demo ou l'API Data Ameli reelle."""
    if Config.APP_MODE == "demo":
        from services.demo_data import DemoDataService
        return DemoDataService()
    return AmeliAPI()
