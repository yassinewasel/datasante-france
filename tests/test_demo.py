import json

from config import Config
from models.db import reconfigure_database


def test_principal_pages_are_database_backed(client):
    for route in ("/", "/indicateurs", "/comparaisons", "/prescriptions", "/honoraires", "/pathologies", "/a-propos"):
        response = client.get(route)
        assert response.status_code == 200
    assert "Donn" in client.get("/").get_data(as_text=True)


def test_region_department_cascade(client):
    payload = client.get("/api/departements/1").get_json()
    assert [row["code"] for row in payload] == ["75", "78"]


def test_map_uses_local_official_geojson(client):
    for path in ("/static/data/regions-france.geojson", "/static/data/departements-france.geojson"):
        response = client.get(path)
        assert response.status_code == 200
        payload = json.loads(response.get_data(as_text=True))
        assert payload["type"] == "FeatureCollection"
        assert {"code", "nom"}.issubset(payload["features"][0]["properties"])


def test_effectif_preview_contains_history(client):
    response = client.get("/api/preview/effectifs?profession_id=1&region_id=1&departement_id=1&annee=2023")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["pret"] is True
    assert payload["effectif"] > 0
    assert len(payload["evolution"]) == 5


def test_analysis_endpoints_return_synthetic_rows(client):
    common = "profession_id=1&region_id=1&departement_id=1&annee_debut=2019&annee_fin=2023"
    cases = (
        (f"/api/analyses/honoraires?{common}&type_honoraire=sans_depassement", "montant_total"),
        (f"/api/analyses/prescriptions?{common}&poste_id=1", "montant_total"),
        ("/api/analyses/pathologies?pathologie=Diabete&region_id=1&departement_id=1&annee_debut=2019&annee_fin=2023", "personnes"),
    )
    for url, key in cases:
        payload = client.get(url).get_json()
        assert payload["pret"] is True
        assert payload[key] > 0
        assert len(payload["donnees"]) == 5


def test_comparison_has_series_and_repartitions(client):
    response = client.get("/api/comparaison/series?profession_a_id=1&profession_b_id=2&region_a_id=1&region_b_id=2&departement_a_id=1&departement_b_id=3&annee_debut=2019&annee_fin=2023")
    payload = response.get_json()
    assert payload["pret"] is True
    assert len(payload["table"]) == 5
    assert payload["series"][0]["donnees"] != payload["series"][1]["donnees"]
    assert payload["repartitions"]["sexes"]["labels"]
    assert payload["repartitions"]["ages"]["labels"]


def test_missing_demo_database_has_helpful_response(client, tmp_path):
    missing = tmp_path / "missing.db"
    Config.DATABASE_URL = f"sqlite:///{missing.as_posix()}"
    reconfigure_database(Config.DATABASE_URL)
    response = client.get("/")
    assert response.status_code == 503
    assert "init_demo_db" in response.get_data(as_text=True)
