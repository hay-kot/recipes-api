import pytest
from fastapi.testclient import TestClient

from pkg import api, core


@pytest.fixture
def auth_client():
    """A client with the API auth key enabled, restored afterwards."""
    settings = core.settings()
    original = settings.auth_key
    settings.auth_key = "s3cret"
    try:
        yield TestClient(api.app)
    finally:
        settings.auth_key = original


def test_missing_key_is_rejected(auth_client: TestClient) -> None:
    resp = auth_client.post("/api/v1/processors/ingredients", json={"ingredients": []})
    assert resp.status_code == 401


def test_wrong_key_is_rejected(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/processors/ingredients",
        json={"ingredients": []},
        headers={"Authorization": "nope"},
    )
    assert resp.status_code == 401


def test_correct_key_is_allowed(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/processors/ingredients",
        json={"ingredients": []},
        headers={"Authorization": "s3cret"},
    )
    assert resp.status_code == 200


def test_readiness_probe_is_exempt(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/system/ready")
    assert resp.status_code == 200


def test_no_auth_key_allows_all(client: TestClient) -> None:
    # default settings leave auth_key empty, so enforcement is disabled
    resp = client.get("/api/system/info")
    assert resp.status_code == 200
