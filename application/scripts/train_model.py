"""Train and evaluate an Iris classifier, then log the experiment to MLflow."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

DEFAULT_EXPERIMENT = "iris-classifier-experiments"
DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"


def git_commit() -> str:
    """Return the current commit when available, including for local dirty experiments."""
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip() or "unknown"


def train(tracking_uri: str, experiment_name: str, neighbors: int) -> str:
    """Train a model and return the MLflow run ID containing its artifacts."""
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    dataset = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data,
        dataset.target,
        test_size=0.2,
        random_state=42,
        stratify=dataset.target,
    )
    model = KNeighborsClassifier(n_neighbors=neighbors, weights="distance")
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="weighted",
        zero_division=0,
    )
    timestamp = datetime.now(UTC).isoformat()
    commit = git_commit()

    with mlflow.start_run() as run, TemporaryDirectory() as artifact_dir:
        mlflow.log_params(
            {
                "algorithm": "KNeighborsClassifier",
                "n_neighbors": neighbors,
                "weights": "distance",
                "test_size": 0.2,
                "random_state": 42,
            }
        )
        mlflow.log_metrics(
            {
                "accuracy": accuracy_score(y_test, predictions),
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
            }
        )
        mlflow.set_tags(
            {
                "git_commit": commit,
                "training_timestamp": timestamp,
                "target_names": json.dumps(dataset.target_names.tolist()),
            }
        )

        artifact_path = Path(artifact_dir)
        (artifact_path / "confusion_matrix.json").write_text(
            json.dumps(confusion_matrix(y_test, predictions).tolist(), indent=2) + "\n"
        )
        (artifact_path / "feature_metadata.json").write_text(
            json.dumps(
                {
                    "feature_names": dataset.feature_names,
                    "target_names": dataset.target_names.tolist(),
                    "training_rows": len(x_train),
                    "evaluation_rows": len(x_test),
                },
                indent=2,
            )
            + "\n"
        )
        mlflow.log_artifacts(artifact_dir, artifact_path="evaluation")
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=infer_signature(x_train, model.predict(x_train)),
            input_example=x_train[:1],
        )
        run_id = run.info.run_id

    print(f"MLflow run created: {run_id}")
    print(f"Register it with: python scripts/register_model.py register --run-id {run_id}")
    return run_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_TRACKING_URI,
    )
    parser.add_argument(
        "--experiment-name",
        default=os.getenv("MLFLOW_EXPERIMENT_NAME") or DEFAULT_EXPERIMENT,
    )
    parser.add_argument("--neighbors", type=int, default=3)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args.tracking_uri, args.experiment_name, args.neighbors)
