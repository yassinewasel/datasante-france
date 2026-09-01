import pytest

from config import Config
from models.db import reconfigure_database
from scripts.init_demo_db import initialize_demo_database


@pytest.fixture()
def client(tmp_path):
    database_path = tmp_path / "demo.db"
    initialize_demo_database(database_path)
    Config.APP_MODE = "demo"
    Config.DATABASE_URL = f"sqlite:///{database_path.as_posix()}"
    reconfigure_database(Config.DATABASE_URL)
    from app import app
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
