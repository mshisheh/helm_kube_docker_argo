# ML API application repository

This directory is intended to be the root of the **application source repository**. It owns the
FastAPI service, model artifact, tests, container definition, and CI workflow. The workflow builds
an image tagged with the immutable Git commit SHA and promotes it only by committing a tag change
to the separate deployment repository.

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/train_model.py
pytest -q
ruff check .
uvicorn app.main:app --reload --port 8080
```

Try an inference:

```bash
curl -s http://localhost:8080/predict \
  -H 'content-type: application/json' \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

## GitHub configuration

Set these Actions variables:

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `my-ml-platform` |
| `GAR_LOCATION` | `us-central1` |
| `GAR_REPOSITORY` | `ml-images` |
| `DEPLOYMENT_REPOSITORY` | `my-org/ml-platform-deploy` |

Set these Actions secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`: full Workload Identity Provider resource name.
- `GCP_SERVICE_ACCOUNT`: CI service-account email allowed to write to Artifact Registry.
- `DEPLOYMENT_REPOSITORY_TOKEN`: fine-grained token or GitHub App token with write access only to
  the deployment repository.

Use GitHub environments and protected branches in a real production setup. Workload Identity
Federation is used instead of a long-lived Google Cloud JSON key.
