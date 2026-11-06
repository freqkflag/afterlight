"""Test fixtures using the live development database with isolated users."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def unique_email():
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def auth_headers(client, unique_email):
    password = "correct-horse-battery"
    reg = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Test User",
        },
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, unique_email, password, login.json()
