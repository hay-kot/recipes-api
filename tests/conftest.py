from fastapi.testclient import TestClient
from pytest import fixture

from main import app


@fixture(scope="session")
def client():
    yield TestClient(app)
