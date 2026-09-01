"""Client pagine pour l'API OpenDataSoft de Data Ameli."""

import time

import requests


BASE_URL = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets"


class DataAmeliClient:
    """Recupere tous les resultats d'une requete, page par page."""

    def __init__(self, http_session=None, page_size=100, timeout=30, pause=0.2):
        self.http = http_session or requests.Session()
        self.page_size = min(page_size, 100)
        self.timeout = timeout
        self.pause = pause

    def collect_all(self, dataset, select=None, where=None, group_by=None):
        url = f"{BASE_URL}/{dataset}/records"
        records = []
        offset = 0

        while True:
            params = {"limit": self.page_size, "offset": offset}
            for key, value in {
                "select": select,
                "where": where,
                "group_by": group_by,
            }.items():
                if value:
                    params[key] = value

            response = self.http.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            page = payload.get("results", [])
            records.extend(page)
            total = payload.get("total_count", len(records))

            if not page or len(records) >= total:
                return records

            offset += self.page_size
            if self.pause:
                time.sleep(self.pause)

