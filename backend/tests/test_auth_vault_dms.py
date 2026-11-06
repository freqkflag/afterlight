"""Core auth, vault, and DMS smoke tests."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_login_refresh(client, unique_email):
    password = "correct-horse-battery"
    reg = client.post(
        "/auth/register",
        json={"email": unique_email, "password": password, "full_name": "Ada"},
    )
    assert reg.status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login.status_code == 200
    body = login.json()
    assert "access_token" in body and "refresh_token" in body

    refreshed = client.post(
        "/auth/refresh",
        json={"refresh_token": body["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    # Refresh token must not work as a bearer access token
    bad = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {body['refresh_token']}"},
    )
    assert bad.status_code == 401


def test_vault_roundtrip(client, auth_headers):
    headers, *_ = auth_headers
    create = client.post(
        "/vault",
        headers=headers,
        json={
            "kind": "note",
            "title_hint": "Test note",
            "encrypted_data": "cipher",
            "nonce": "nonce",
        },
    )
    assert create.status_code == 201
    item = create.json()
    assert item["encrypted_data"] == "cipher"

    listed = client.get("/vault", headers=headers)
    assert listed.status_code == 200
    assert any(i["id"] == item["id"] for i in listed.json())


def test_dms_configure_and_check_in(client, auth_headers):
    headers, *_ = auth_headers
    cfg = client.post(
        "/dead-mans-switch/configure",
        headers=headers,
        json={"check_in_interval_days": 14, "grace_period_days": 7},
    )
    assert cfg.status_code == 200
    assert cfg.json()["check_in_interval_days"] == 14

    check = client.post(
        "/dead-mans-switch/check-in",
        headers=headers,
        json={"method": "app"},
    )
    assert check.status_code == 200

    status = client.get("/dead-mans-switch/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "active"


def test_executor_invite_and_portal(client, unique_email):
    owner_email = unique_email
    executor_email = f"exec-{unique_email}"
    password = "correct-horse-battery"

    client.post(
        "/auth/register",
        json={"email": owner_email, "password": password, "full_name": "Owner"},
    )
    owner_login = client.post(
        "/auth/login",
        json={"email": owner_email, "password": password},
    )
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    invite = client.post(
        "/executor",
        headers=owner_headers,
        json={
            "executor_email": executor_email,
            "executor_name": "Exec",
            "relationship": "sibling",
        },
    )
    assert invite.status_code == 201
    executor_id = invite.json()["id"]

    client.post(
        "/auth/register",
        json={"email": executor_email, "password": password, "full_name": "Exec"},
    )
    exec_login = client.post(
        "/auth/login",
        json={"email": executor_email, "password": password},
    )
    exec_headers = {"Authorization": f"Bearer {exec_login.json()['access_token']}"}

    pending = client.get("/executor/portal/estates", headers=exec_headers)
    assert pending.status_code == 200
    assert len(pending.json()) == 1

    accepted = client.post(
        "/executor/portal/accept",
        headers=exec_headers,
        json={"executor_id": executor_id},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "active"
