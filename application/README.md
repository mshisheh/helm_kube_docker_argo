# ML API application repository

This directory is intended to be the root of the **application source repository**. It owns the
FastAPI service, MLflow experiment/registry scripts, exported production model, tests, container
definition, and CI workflow. MLflow selects the approved model; GitHub Actions packages it; GitOps
and Argo CD remain the only deployment path.

## Model lifecycle

The default local tracking backend is SQLite (`sqlite:///mlflow.db`). Override it with
`MLFLOW_TRACKING_URI` when using a shared tracking server.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt

# 1. Train, evaluate, and log an experiment. Note the printed run ID.
python scripts/train_model.py --neighbors 3

# 2. Register the run as a new non-production model version.
python scripts/register_model.py register --run-id RUN_ID

# 3. Review metrics/artifacts in the UI.
mlflow ui --backend-store-uri sqlite:///mlflow.db

# 4. Manually promote the reviewed version. This archives the previous Production version.
python scripts/register_model.py promote --version VERSION

# 5. Reproduce the CI export locally.
python scripts/register_model.py export-production
```

Training logs algorithm parameters; accuracy, weighted precision, recall, and F1 metrics; the
scikit-learn model; a confusion matrix; and feature metadata. Registration and promotion are
separate commands so metrics never trigger automatic production approval. The application itself
does not import or contact MLflow at runtime.

`models/current/` is intentionally empty in Git. The export command writes exactly one deployment
artifact and its metadata there. CI performs that export from the current MLflow Production version
before every image build; tests generate isolated temporary artifacts instead of committing a binary
model to the repository.

## Local development

```bash
pytest -q
ruff check .
uvicorn app.main:app --reload --port 8080
```

Try an inference and inspect both deployed versions:

```bash
curl -s http://localhost:8080/predict \
  -H 'content-type: application/json' \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
curl -s http://localhost:8080/version
```

## GitHub configuration

Set these Actions variables:

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `my-ml-platform` |
| `GAR_LOCATION` | `us-central1` |
| `GAR_REPOSITORY` | `ml-images` |
| `DEPLOYMENT_REPOSITORY` | `my-org/ml-platform-deploy` |
| `MLFLOW_TRACKING_URI` | `https://mlflow.example.com` |
| `MLFLOW_MODEL_NAME` | `iris-classifier` |

Set these Actions secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`: full Workload Identity Provider resource name.
- `GCP_SERVICE_ACCOUNT`: CI service-account email allowed to write to Artifact Registry.
- `DEPLOYMENT_REPOSITORY_TOKEN`: fine-grained token or GitHub App token with write access only to
  the deployment repository.
- `MLFLOW_TRACKING_USERNAME` and `MLFLOW_TRACKING_PASSWORD`: optional credentials for a protected
  tracking server. Prefer the authentication mechanism required by the selected backend.

A local SQLite backend is suitable for demonstrating training, registration, review, and export on
one machine. GitHub Actions requires a reachable, persistent tracking server (or equivalent managed
backend) containing the approved version.

The build job downloads only the model in the `Production` stage and writes
`models/current/model.pkl` plus `metadata.json`. It never trains or promotes a model. It then builds
an immutable image tagged with the Git SHA and commits that SHA to the deployment repository.
Workload Identity Federation is used instead of a long-lived Google Cloud JSON key.
