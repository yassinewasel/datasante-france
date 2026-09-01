# Pipeline Data Ameli

Le depot reunit maintenant les deux parties du projet : le travail de donnees de la SAE 2.04 et l'application Flask qui les exploite.

```text
API Data Ameli
      |
      v
pagination et selection des champs (etl/client.py)
      |
      v
nettoyage, dedoublonnage et relations (etl/collectors.py)
      |
      v
9 tables de dimensions SQLAlchemy
      |
      v
services Flask -> API interne -> cartes, graphiques et tableaux
```

## Dimensions chargees

- geographie : regions et departements ;
- professionnels : professions, tranches d'age et sexes ;
- activite : types d'exercice et secteurs conventionnels ;
- finance : types d'honoraires et postes de prescription.

Les collecteurs sont idempotents : une seconde execution ne duplique pas les valeurs deja presentes. Le departement technique `999` de Data Ameli est exclu.

## Utilisation sure

Configurer une base destinee aux donnees reelles dans `.env`, puis lancer :

```powershell
$env:APP_MODE = "real"
$env:DATABASE_URL = "mysql+pymysql://utilisateur:mot-de-passe@localhost/datasante"
python -m etl.pipeline --collect
```

Sans `--collect`, la commande effectue seulement la creation des tables manquantes et les controles locaux : aucun appel reseau et aucune suppression.

La reconstruction complete est volontairement protegee par deux options explicites :

```powershell
python -m etl.pipeline --collect --reset --yes
```

Cette derniere commande supprime les tables de la base configuree avant de les recreer. Elle ne doit jamais etre lancee sur une base a conserver.

