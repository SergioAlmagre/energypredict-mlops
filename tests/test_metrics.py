def test_metrics_endpoint_exposes_prometheus_text(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "energypredict_http_requests_total" in response.text
