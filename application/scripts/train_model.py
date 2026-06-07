"""Build the deterministic JSON model artifact shipped in the image."""

import json
from pathlib import Path

from sklearn.datasets import load_iris

MODEL_VERSION = "iris-knn-v1"
TRAINING_ROWS = [0, 1, 6, 50, 61, 65, 100, 102, 104]


def train(output_path: Path) -> None:
    dataset = load_iris()
    artifact = {
        "model_type": "KNeighborsClassifier",
        "model_version": MODEL_VERSION,
        "n_neighbors": 3,
        "target_names": dataset.target_names.tolist(),
        "features": dataset.data[TRAINING_ROWS].tolist(),
        "targets": dataset.target[TRAINING_ROWS].tolist(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"Saved {MODEL_VERSION} to {output_path}")


if __name__ == "__main__":
    train(Path("model/iris.json"))
