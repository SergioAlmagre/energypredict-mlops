def test_register_and_login_success(client):
    email = "auth_ok@example.com"
    password = "StrongPassword123!"

    register_resp = client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "consumer"})
    assert register_resp.status_code == 201

    login_resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_login_incorrect_password(client):
    email = "auth_fail@example.com"
    password = "StrongPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "consumer"})

    bad_login = client.post("/api/v1/auth/login", data={"username": email, "password": "WrongPassword"})
    assert bad_login.status_code == 401


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": "StrongPassword123!", "role": "consumer"}
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_auth_me_returns_current_user(client):
    email = "me_user@example.com"
    password = "StrongPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "consumer"})
    login_resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = login_resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["email"] == email
    assert body["role"] == "consumer"


def test_login_bruteforce_lock_after_repeated_failures(client):
    email = "lock_user@example.com"
    password = "StrongPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "consumer"})

    for _ in range(5):
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "WrongPassword"})
        assert resp.status_code == 401

    locked = client.post("/api/v1/auth/login", data={"username": email, "password": "WrongPassword"})
    assert locked.status_code == 429


def test_login_success_resets_failed_attempts_counter(client):
    email = "reset_user@example.com"
    password = "StrongPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "consumer"})

    for _ in range(3):
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "WrongPassword"})
        assert resp.status_code == 401

    ok = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert ok.status_code == 200
