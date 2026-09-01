"""Configuration de DataSante."""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuration commune aux modes demo et donnees reelles."""

    APP_MODE = os.getenv("APP_MODE", "demo").lower()
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'data' / 'datasante_demo.db').as_posix()}",
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-only-change-me")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    ANNEE_DEBUT = 2019
    ANNEE_FIN = 2023
    ANNEES = list(range(ANNEE_FIN, ANNEE_DEBUT - 1, -1))

    @classmethod
    def annee_valide(cls, annee):
        return annee in cls.ANNEES

    @classmethod
    def db_url(cls):
        return cls.DATABASE_URL

    @classmethod
    def demo_database_path(cls):
        prefix = "sqlite:///"
        return Path(cls.DATABASE_URL[len(prefix):]) if cls.DATABASE_URL.startswith(prefix) else None
