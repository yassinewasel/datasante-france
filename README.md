# DataSante

Application Flask d'exploration et de comparaison de donnees de sante en France. Le depot propose une demonstration SQLite reproductible et hors ligne, ainsi qu'un mode reel configurable utilisant l'API Data Ameli.

## Fonctionnalites

- filtres region, departement, profession et periode ;
- effectifs, densites, honoraires, prescriptions et pathologies ;
- comparaisons, graphiques Chart.js, tableaux et carte Leaflet ;
- base de demonstration synthetique generee localement ;
- client Data Ameli conserve pour un usage reel explicite.

## Demarrage rapide - PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.init_demo_db
python -m flask --app app run
```

Linux, macOS ou WSL :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.init_demo_db
python -m flask --app app run
```

La base `data/datasante_demo.db` est ignoree par Git. Toutes ses mesures sont synthetiques et ne sont pas des valeurs Data Ameli.

Pour la recreer :

```powershell
python -m scripts.init_demo_db --force
```

## Mode reel

Definir `APP_MODE=real` et `DATABASE_URL` vers une base SQLAlchemy compatible. Dans ce mode, les mesures sont demandees a Data Ameli ; aucune collecte reelle n'est executee automatiquement.

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest -v -p no:cacheprovider
```

## Projet collectif et contribution

Le projet initial a ete realise par Abdelwadoud Alloune, Abdou Apela Akunde, Djibril Berriche et Yassine Wasel dans le cadre du BUT Informatique.

Contributions documentees de Yassine Wasel : maquette et structure UX, collecte des dimensions `type_exercice` et `type_secteur` avec Requests et SQLAlchemy, deduplication, documentation, tests Flask limites et preparation de presentation. Le README historique attribue aussi a Yassine une contribution a la page Comparaisons et a ses graphiques Chart.js, sans historique assez granulaire pour attribuer chaque ligne.

Cette edition nettoyee ne revendique pas comme travail individuel les autres fonctionnalites collectives.

## Donnees et licences

Voir [docs/data-sources.md](docs/data-sources.md). Data Ameli et les contours administratifs sont sous ODbL 1.0. Chart.js est sous MIT et Leaflet sous BSD-2-Clause.

La licence du code collectif doit etre choisie avec l'accord des quatre coauteurs avant publication publique.
