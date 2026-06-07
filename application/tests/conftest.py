import json
from datetime import UTC, datetime

import joblib
import pytest
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

from app.main import settings


@pytest.fixture(autouse=True)
def packaged_model(tmp_path, monkeypatch):
    """Generate the packaged model fixture that CI normally exports from MLflow."""
    dataset = load_iris()
    model = KNeighborsClassifier(n_neighbors=3, weights="distance")
    model.fit(dataset.data, dataset.target)

    model_path = tmp_path / "model.pkl"
    metadata_path = tmp_path / "metadata.json"
    joblib.dump(model, model_path)
    metadata_path.write_text(
        json.dumps(
            {
                "model_name": "iris-classifier",
                "model_version": "1",
                "training_timestamp": datetime.now(UTC).isoformat(),
                "git_commit": "test-commit",
                "experiment_run_id": "test-mlflow-run",
                "target_names": dataset.target_names.tolist(),
            }
        )
    )

    monkeypatch.setattr(settings, "model_path", str(model_path))
    monkeypatch.setattr(settings, "model_metadata_path", str(metadata_path))
