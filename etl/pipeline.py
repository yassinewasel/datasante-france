"""Point d'entree securise du pipeline Data Ameli."""

import argparse
import json

from config import Config
from etl.client import DataAmeliClient
from etl.collectors import collect_all_dimensions
from etl.verify import dimension_counts, orphan_department_codes
from models.db import Session, engine
from models.dimensions import Base


def run_pipeline(session, client):
    """Cree les tables manquantes et collecte sans supprimer l'existant."""
    Base.metadata.create_all(engine)
    collect_all_dimensions(session, client)
    return dimension_counts(session)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collect",
        action="store_true",
        help="autorise les appels reseau et le chargement idempotent",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="supprime d'abord toutes les tables (necessite --yes)",
    )
    parser.add_argument("--yes", action="store_true", help="confirme --reset")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.reset and not (args.collect and args.yes):
        raise SystemExit("--reset exige --collect --yes")
    if args.collect and Config.APP_MODE != "real":
        raise SystemExit("La collecte reseau exige APP_MODE=real")

    if args.reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session = Session()
    try:
        if args.collect:
            collect_all_dimensions(session, DataAmeliClient())
        report = {
            "dimensions": dimension_counts(session),
            "departements_sans_region": orphan_department_codes(session),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()

