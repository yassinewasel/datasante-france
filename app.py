"""Point d'entree de l'application Flask."""

from flask import Flask, render_template, request
from config import Config
from controllers.accueil import bp_accueil
from controllers.api import bp_api
from controllers.dashboard import bp_dashboard


app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(bp_accueil)
app.register_blueprint(bp_api)
app.register_blueprint(bp_dashboard)


@app.before_request
def verifier_base_demo():
    """Explique comment initialiser la demo au lieu d'exposer une erreur SQL."""
    path = Config.demo_database_path()
    if Config.APP_MODE == "demo" and path and not path.exists() and request.endpoint != "static":
        return render_template(
            "erreur.html",
            message="Base de demonstration absente. Executez : python -m scripts.init_demo_db",
        ), 503


@app.context_processor
def mode_application():
    return {"demo_mode": Config.APP_MODE == "demo"}


@app.errorhandler(404)
def page_non_trouvee(_erreur):
    """Affiche une page claire pour une URL inconnue."""
    return render_template("erreur.html", message="Page non trouvée."), 404


@app.errorhandler(500)
def erreur_serveur(_erreur):
    """Affiche une page claire lors d'une erreur serveur."""
    return render_template(
        "erreur.html",
        message="Erreur interne. Réessayez plus tard.",
    ), 500


if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
