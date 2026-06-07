from fastapi.testclient import TestClient

from app.main import app


def test_health_and_readiness() -> None:
    with TestClient(app) as client:
        health = client.get("/healthz")
        readiness = client.get("/readyz")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "model_loaded": True}
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready", "model_loaded": True}


def test_predict_setosa() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["class_id"] == 0
    assert body["class_name"] == "setosa"
    assert body["model_version"] == "1"
    assert abs(sum(body["probabilities"].values()) - 1) < 0.00001


def test_invalid_features_are_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "sepal_length": -1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

    assert response.status_code == 422


def test_version_reports_application_and_model_identity(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.app_version", "test-sha")
    with TestClient(app) as client:
        response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "application_version": "test-sha",
        "model_name": "iris-classifier",
        "model_version": "1",
        "mlflow_run_id": "test-mlflow-run",
    }
