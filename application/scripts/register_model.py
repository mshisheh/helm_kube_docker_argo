"""Register, manually promote, or export an MLflow model for deployment."""

import argparse
import json
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient

DEFAULT_MODEL_NAME = "iris-classifier"
DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"


def client_for(tracking_uri: str) -> MlflowClient:
    mlflow.set_tracking_uri(tracking_uri)
    return MlflowClient()


def register(run_id: str, model_name: str, tracking_uri: str) -> str:
    """Register a run's model without promoting it to Production."""
    client = client_for(tracking_uri)
    try:
        client.get_registered_model(model_name)
    except mlflow.exceptions.MlflowException as error:
        if error.error_code != "RESOURCE_DOES_NOT_EXIST":
            raise
        client.create_registered_model(model_name)

    version = client.create_model_version(
        name=model_name,
        source=f"runs:/{run_id}/model",
        run_id=run_id,
        tags={"approval_status": "pending"},
    )
    print(f"Registered {model_name} version {version.version} in non-production state")
    return version.version


def promote(model_name: str, version: str, tracking_uri: str) -> None:
    """Manually transition one reviewed model version to Production."""
    client = client_for(tracking_uri)
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
        archive_existing_versions=True,
    )
    client.set_model_version_tag(model_name, version, "approval_status", "approved")
    print(f"Promoted {model_name} version {version} to Production")


def export_production(
    model_name: str,
    output_dir: Path,
    tracking_uri: str,
) -> dict[str, object]:
    """Export the single Production model and deployment metadata for the image build."""
    client = client_for(tracking_uri)
    production_versions = client.get_latest_versions(model_name, stages=["Production"])
    if len(production_versions) != 1:
        raise RuntimeError(
            f"Expected exactly one Production version for {model_name}; "
            f"found {len(production_versions)}"
        )

    version = production_versions[0]
    run = client.get_run(version.run_id)
    model = mlflow.sklearn.load_model(f"models:/{model_name}/{version.version}")
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / "model.pkl")

    metadata = {
        "model_name": model_name,
        "model_version": str(version.version),
        "training_timestamp": run.data.tags.get("training_timestamp", "unknown"),
        "git_commit": run.data.tags.get("git_commit", "unknown"),
        "experiment_run_id": version.run_id,
        "target_names": json.loads(run.data.tags.get("target_names", "[]")),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Exported {model_name} version {version.version} to {output_dir}")
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_TRACKING_URI,
    )
    parser.add_argument(
        "--model-name",
        default=os.getenv("MLFLOW_MODEL_NAME") or DEFAULT_MODEL_NAME,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    register_parser = commands.add_parser("register", help="Register a completed training run")
    register_parser.add_argument("--run-id", required=True)

    promote_parser = commands.add_parser("promote", help="Manually promote a reviewed version")
    promote_parser.add_argument("--version", required=True)

    export_parser = commands.add_parser("export-production", help="Export the Production version")
    export_parser.add_argument("--output-dir", type=Path, default=Path("models/current"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.command == "register":
        register(args.run_id, args.model_name, args.tracking_uri)
    elif args.command == "promote":
        promote(args.model_name, args.version, args.tracking_uri)
    else:
        export_production(args.model_name, args.output_dir, args.tracking_uri)
