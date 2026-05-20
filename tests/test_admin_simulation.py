def test_admin_simulation_controls_require_admin(client, consumer_headers):
    response = client.post("/api/v1/admin/simulation/start", headers=consumer_headers)
    assert response.status_code == 403


def test_admin_simulation_start_status_stop(client, admin_headers):
    start_response = client.post("/api/v1/admin/simulation/start", headers=admin_headers)
    assert start_response.status_code == 200
    assert start_response.json()["is_running"] is True

    status_response = client.get("/api/v1/admin/simulation/status", headers=admin_headers)
    assert status_response.status_code == 200
    assert status_response.json()["is_running"] is True

    stop_response = client.post("/api/v1/admin/simulation/stop", headers=admin_headers)
    assert stop_response.status_code == 200
    assert stop_response.json()["is_running"] is False
