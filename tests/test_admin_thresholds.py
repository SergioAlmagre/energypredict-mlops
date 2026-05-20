def test_risk_thresholds_requires_authentication(client):
    response = client.get("/api/v1/admin/risk-thresholds")
    assert response.status_code == 401


def test_non_admin_cannot_manage_thresholds(client, consumer_headers):
    get_resp = client.get("/api/v1/admin/risk-thresholds", headers=consumer_headers)
    assert get_resp.status_code == 403

    put_resp = client.put(
        "/api/v1/admin/risk-thresholds",
        json={"low_max": 0.2, "medium_max": 0.6},
        headers=consumer_headers,
    )
    assert put_resp.status_code == 403


def test_admin_can_get_and_update_thresholds(client, admin_headers):
    get_resp = client.get("/api/v1/admin/risk-thresholds", headers=admin_headers)
    assert get_resp.status_code == 200
    original = get_resp.json()
    assert original["low_max"] < original["medium_max"]

    put_resp = client.put(
        "/api/v1/admin/risk-thresholds",
        json={"low_max": 0.1, "medium_max": 0.4},
        headers=admin_headers,
    )
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["low_max"] == 0.1
    assert updated["medium_max"] == 0.4
    assert updated["updated_by_user_id"]


def test_threshold_update_validates_order(client, admin_headers):
    response = client.put(
        "/api/v1/admin/risk-thresholds",
        json={"low_max": 0.7, "medium_max": 0.7},
        headers=admin_headers,
    )
    assert response.status_code == 422

