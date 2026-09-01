"""API JSON utilisee par les filtres et les graphiques."""

from flask import Blueprint, jsonify, request
import re

from config import Config
from models.db import Session
from models.dimensions import (
    Departement,
    ProfessionSante,
    Region,
    TypePrescription,
)
from services.ameli_api import create_data_service
from services.analytics import analyser_evolution


bp_api = Blueprint("api", __name__, url_prefix="/api")
api_ameli = create_data_service()

HONORAIRES_TYPES = {
    "sans_depassement": {
        "libelle": "Honoraires sans dépassement",
        "total": "hono_sans_depassement_totaux_integer",
        "moyen": "hono_sans_depassement_moyens_integer",
    },
    "depassements": {
        "libelle": "Dépassements d'honoraires",
        "total": "depassements_totaux_integer",
        "moyen": "depassements_moyens_integer",
    },
}


def _periode_recue(request):
    """Lit et valide une periode transmise dans la requete."""
    annee_debut = request.args.get("annee_debut", type=int)
    annee_fin = request.args.get("annee_fin", type=int)
    if not Config.annee_valide(annee_debut) or not Config.annee_valide(annee_fin):
        return None, None, "La période doit être comprise entre 2015 et 2023."
    if annee_debut > annee_fin:
        return None, None, "L'année de début doit précéder l'année de fin."
    return annee_debut, annee_fin, None


def _territoire(session, region_id, departement_id):
    """Verifie qu'un departement appartient a la region demandee."""
    region = session.get(Region, region_id)
    departement = session.get(Departement, departement_id) if departement_id else None
    if not region or (departement and departement.region_id != region.id):
        return None, None
    return region, departement


def _libelle_region(region):
    """Retourne le libelle de region pour l'affichage."""
    return "Île-de-France" if region.libelle == "Ile-de-France" else region.libelle


def _resume_montants(rows, total_key, moyen_key):
    """Prepare les montants annuels et leurs totaux."""
    lignes = []
    for row in rows:
        lignes.append(
            {
                "annee": row.get("annee"),
                "montant_total": row.get(total_key) or 0,
                "montant_moyen": row.get(moyen_key) or 0,
            }
        )
    totaux = [row["montant_total"] for row in lignes]
    moyens = [row["montant_moyen"] for row in lignes]
    return lignes, sum(totaux), (sum(moyens) / len(moyens) if moyens else 0)


def _repartition(rows, label_key, ignore_labels=(), ordre=None):
    """Transforme une repartition API en labels et valeurs."""
    valeurs = {
        row.get(label_key): row.get("effectif") or 0
        for row in rows
        if row.get(label_key) and row.get(label_key) not in ignore_labels
    }
    labels = list(valeurs)
    if ordre:
        labels.sort(key=ordre)
    else:
        labels.sort()
    return labels, valeurs


@bp_api.route("/departements/<int:region_id>")
def departements(region_id):
    """Retourne les départements d'une région au format JSON."""
    session = Session()
    try:
        depts = (
            session.query(Departement)
            .filter_by(region_id=region_id)
            .order_by(Departement.code)
            .all()
        )
        return jsonify([d.to_dict() for d in depts])
    finally:
        session.close()


@bp_api.route("/preview/effectifs")
def preview_effectifs():
    """Prévisualisation de l'accueil : KPI + évolution pour les filtres choisis."""
    profession_id = request.args.get("profession_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    if annee and not Config.annee_valide(annee):
        return jsonify({"pret": False, "message": f"Année invalide ({Config.ANNEE_DEBUT}-{Config.ANNEE_FIN})."}), 400
    if not profession_id or not region_id or not annee:
        return jsonify({"pret": False, "message": "Sélection incomplète."})

    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        region, dept = _territoire(session, region_id, departement_id)
        if not prof or not region:
            return jsonify({"pret": False, "message": "Sélection incomplète."})

        if dept:
            resultats = api_ameli.get_effectifs(prof.libelle, dept.code, annee)
            evolution = api_ameli.get_evolution_effectifs(prof.libelle, dept.code)
            territoire = dept.to_dict()
        else:
            evolution = api_ameli.get_effectifs_territoire(
                prof.libelle, region.code, None, Config.ANNEE_DEBUT, Config.ANNEE_FIN
            )
            resultats = [row for row in evolution if str(row.get("annee", ""))[:4] == str(annee)]
            territoire = {"code": region.code, "libelle": _libelle_region(region)}
        evolution = [
            row
            for row in evolution
            if str(row.get("annee", ""))[:4].isdigit()
            and Config.annee_valide(int(str(row["annee"])[:4]))
        ]
        analyse = analyser_evolution(evolution, annee)
        ligne = resultats[0] if resultats else {}
        return jsonify(
            {
                "pret": True,
                "profession": prof.libelle,
                "departement": territoire,
                "annee": annee,
                "effectif": ligne.get("effectif"),
                "densite": ligne.get("densite"),
                "resultats": resultats,
                "evolution": evolution,
                "analyse": analyse,
                "erreur": api_ameli.derniere_erreur,
            }
        )
    finally:
        session.close()


@bp_api.route("/analyses/honoraires")
def analyse_honoraires():
    """Renvoie les honoraires correspondant aux filtres choisis."""
    profession_id = request.args.get("profession_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    type_honoraire = request.args.get("type_honoraire")
    annee_debut, annee_fin, erreur = _periode_recue(request)
    type_selectionne = HONORAIRES_TYPES.get(type_honoraire)
    if erreur or not profession_id or not region_id or not type_selectionne:
        return jsonify({"pret": False, "message": erreur or "Sélection incomplète."}), 400

    session = Session()
    try:
        profession = session.get(ProfessionSante, profession_id)
        region, departement = _territoire(session, region_id, departement_id)
        if not profession or not region:
            return jsonify({"pret": False, "message": "Territoire ou profession invalide."}), 400
        rows = api_ameli.get_honoraires(
            profession.libelle,
            region.code,
            departement.code if departement else None,
            annee_debut,
            annee_fin,
        )
        lignes, montant_total, montant_moyen = _resume_montants(
            rows, type_selectionne["total"], type_selectionne["moyen"]
        )
        return jsonify(
            {
                "pret": True,
                "profession": profession.libelle,
                "type_honoraire": type_selectionne["libelle"],
                "territoire": departement.libelle if departement else _libelle_region(region),
                "periode": {"debut": annee_debut, "fin": annee_fin},
                "montant_total": montant_total,
                "montant_moyen": montant_moyen,
                "donnees": lignes,
                "erreur": api_ameli.derniere_erreur,
            }
        )
    finally:
        session.close()


@bp_api.route("/analyses/prescriptions")
def analyse_prescriptions():
    """Renvoie les prescriptions correspondant aux filtres choisis."""
    profession_id = request.args.get("profession_id", type=int)
    poste_id = request.args.get("poste_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee_debut, annee_fin, erreur = _periode_recue(request)
    if erreur or not profession_id or not poste_id or not region_id:
        return jsonify({"pret": False, "message": erreur or "Sélection incomplète."}), 400

    session = Session()
    try:
        profession = session.get(ProfessionSante, profession_id)
        poste = session.get(TypePrescription, poste_id)
        region, departement = _territoire(session, region_id, departement_id)
        if not profession or not poste or not region:
            return jsonify({"pret": False, "message": "Sélection invalide."}), 400
        rows = api_ameli.get_prescriptions(
            profession.libelle,
            poste.libelle,
            region.code,
            departement.code if departement else None,
            annee_debut,
            annee_fin,
        )
        lignes, montant_total, montant_moyen = _resume_montants(
            rows, "montant_total_prescription_integer", "montant_moyen_prescription_integer"
        )
        return jsonify(
            {
                "pret": True,
                "profession": profession.libelle,
                "poste": poste.libelle,
                "territoire": departement.libelle if departement else _libelle_region(region),
                "periode": {"debut": annee_debut, "fin": annee_fin},
                "montant_total": montant_total,
                "montant_moyen": montant_moyen,
                "donnees": lignes,
                "erreur": api_ameli.derniere_erreur,
            }
        )
    finally:
        session.close()


@bp_api.route("/analyses/pathologies")
def analyse_pathologies():
    """Renvoie les effectifs et la prevalence d'une pathologie."""
    pathologie = request.args.get("pathologie")
    region_id = request.args.get("region_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee_debut, annee_fin, erreur = _periode_recue(request)
    if erreur or not pathologie or not region_id:
        return jsonify({"pret": False, "message": erreur or "Sélection incomplète."}), 400

    session = Session()
    try:
        region, departement = _territoire(session, region_id, departement_id)
        if not region:
            return jsonify({"pret": False, "message": "Territoire invalide."}), 400
        rows = api_ameli.get_pathologie_effectifs(
            pathologie,
            region.code,
            departement.code if departement else None,
            annee_debut,
            annee_fin,
        )
        lignes = [
            {
                "annee": str(row.get("annee", ""))[:4],
                "personnes": row.get("ntop") or 0,
                "population": row.get("npop") or 0,
                "prevalence": round(
                    ((row.get("ntop") or 0) / (row.get("npop") or 1)) * 100, 3
                ),
            }
            for row in rows
        ]
        dernier = lignes[-1] if lignes else {}
        return jsonify(
            {
                "pret": True,
                "pathologie": pathologie,
                "territoire": departement.libelle if departement else _libelle_region(region),
                "periode": {"debut": annee_debut, "fin": annee_fin},
                "personnes": dernier.get("personnes", 0),
                "prevalence": dernier.get("prevalence", 0),
                "donnees": lignes,
                "erreur": api_ameli.derniere_erreur,
            }
        )
    finally:
        session.close()


@bp_api.route("/comparaison/series")
def comparaison_series():
    """Construit deux series comparables et leurs repartitions."""
    profession_a_id = request.args.get("profession_a_id", type=int)
    profession_b_id = request.args.get("profession_b_id", type=int)
    region_a_id = request.args.get("region_a_id", type=int)
    region_b_id = request.args.get("region_b_id", type=int)
    departement_a_id = request.args.get("departement_a_id", type=int)
    departement_b_id = request.args.get("departement_b_id", type=int)
    annee_debut, annee_fin, erreur = _periode_recue(request)
    if erreur or not all([profession_a_id, profession_b_id, region_a_id, region_b_id]):
        return jsonify({"pret": False, "message": erreur or "Sélection incomplète."}), 400

    session = Session()
    try:
        profession_a = session.get(ProfessionSante, profession_a_id)
        profession_b = session.get(ProfessionSante, profession_b_id)
        region_a, departement_a = _territoire(session, region_a_id, departement_a_id)
        region_b, departement_b = _territoire(session, region_b_id, departement_b_id)
        if not all([profession_a, profession_b, region_a, region_b]):
            return jsonify({"pret": False, "message": "Sélection invalide."}), 400

        donnees_a = api_ameli.get_effectifs_territoire(
            profession_a.libelle,
            region_a.code,
            departement_a.code if departement_a else None,
            annee_debut,
            annee_fin,
        )
        erreur_a = api_ameli.derniere_erreur
        donnees_b = api_ameli.get_effectifs_territoire(
            profession_b.libelle,
            region_b.code,
            departement_b.code if departement_b else None,
            annee_debut,
            annee_fin,
        )
        erreur_b = api_ameli.derniere_erreur
        repartition_a = api_ameli.get_repartitions_effectifs(
            profession_a.libelle,
            region_a.code,
            departement_a.code if departement_a else None,
            annee_fin,
        )
        erreur_repartition_a = api_ameli.derniere_erreur
        repartition_b = api_ameli.get_repartitions_effectifs(
            profession_b.libelle,
            region_b.code,
            departement_b.code if departement_b else None,
            annee_fin,
        )
        erreur_repartition_b = api_ameli.derniere_erreur

        def normaliser(rows):
            """Indexe les lignes API par annee."""
            return {
                str(row.get("annee", ""))[:4]: {
                    "effectif": row.get("effectif") or 0,
                    "densite": row.get("densite") or 0,
                }
                for row in rows
            }

        serie_a = normaliser(donnees_a)
        serie_b = normaliser(donnees_b)
        annees = [str(annee) for annee in range(annee_debut, annee_fin + 1)]
        table = [
            {
                "annee": annee,
                "effectif_a": serie_a.get(annee, {}).get("effectif", 0),
                "densite_a": serie_a.get(annee, {}).get("densite", 0),
                "effectif_b": serie_b.get(annee, {}).get("effectif", 0),
                "densite_b": serie_b.get(annee, {}).get("densite", 0),
            }
            for annee in annees
        ]
        libelle_a = f"{profession_a.libelle} - {departement_a.libelle if departement_a else _libelle_region(region_a)}"
        libelle_b = f"{profession_b.libelle} - {departement_b.libelle if departement_b else _libelle_region(region_b)}"
        dernier_a = next((row for row in reversed(table) if row["effectif_a"]), table[-1])
        dernier_b = next((row for row in reversed(table) if row["effectif_b"]), table[-1])

        sexes_a_labels, sexes_a = _repartition(
            repartition_a["sexes"], "libelle_sexe", {"tout sexe", "sexe inconnu"}
        )
        sexes_b_labels, sexes_b = _repartition(
            repartition_b["sexes"], "libelle_sexe", {"tout sexe", "sexe inconnu"}
        )
        sexes_labels = sorted(set(sexes_a_labels) | set(sexes_b_labels))

        def ordre_age(label):
            """Extrait le premier age pour trier les libelles."""
            match = re.search(r"\d+", label)
            return int(match.group()) if match else 999

        ages_a_labels, ages_a = _repartition(
            repartition_a["ages"], "libelle_classe_age", {"Tout âge"}, ordre_age
        )
        ages_b_labels, ages_b = _repartition(
            repartition_b["ages"], "libelle_classe_age", {"Tout âge"}, ordre_age
        )
        ages_labels = sorted(set(ages_a_labels) | set(ages_b_labels), key=ordre_age)
        return jsonify(
            {
                "pret": True,
                "periode": {"debut": annee_debut, "fin": annee_fin},
                "series": [
                    {"label": libelle_a, "donnees": [row["effectif_a"] for row in table]},
                    {"label": libelle_b, "donnees": [row["effectif_b"] for row in table]},
                ],
                "annees": annees,
                "derniers": [
                    {"label": libelle_a, "effectif": dernier_a["effectif_a"], "densite": dernier_a["densite_a"]},
                    {"label": libelle_b, "effectif": dernier_b["effectif_b"], "densite": dernier_b["densite_b"]},
                ],
                "table": table,
                "repartitions": {
                    "sexes": {
                        "labels": sexes_labels,
                        "a": [sexes_a.get(label, 0) for label in sexes_labels],
                        "b": [sexes_b.get(label, 0) for label in sexes_labels],
                    },
                    "ages": {
                        "labels": ages_labels,
                        "a": [ages_a.get(label, 0) for label in ages_labels],
                        "b": [ages_b.get(label, 0) for label in ages_labels],
                    },
                },
                "erreur": erreur_a or erreur_b or erreur_repartition_a or erreur_repartition_b,
            }
        )
    finally:
        session.close()
