from fastapi.testclient import TestClient
from pytest import fixture

from pkg import api


@fixture(scope="session")
def client():
    yield TestClient(api.app)
