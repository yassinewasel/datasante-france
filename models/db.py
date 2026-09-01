"""Connexion SQLAlchemy partagee par l'application."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config


engine = create_engine(Config.db_url(), pool_recycle=3600)
Session = sessionmaker(bind=engine)


def reconfigure_database(database_url):
    """Reconfigure la connexion, principalement pour les tests isoles."""
    global engine
    engine.dispose()
    engine = create_engine(database_url, pool_recycle=3600)
    Session.configure(bind=engine)
    return engine
