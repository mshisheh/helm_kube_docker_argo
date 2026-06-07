import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram, make_asgi_app

from app.schemas import HealthResponse, IrisFeatures, PredictionResponse, VersionResponse
from app.settings import get_settings

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS = Counter(
    "ml_api_predictions_total",
    "Number of prediction requests.",
    ["predicted_class"],
)
PREDICTION_LATENCY = Histogram(
    "ml_api_prediction_duration_seconds",
    "Prediction request duration in seconds.",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    model_path = Path(settings.model_path)
    metadata_path = Path(settings.model_metadata_path)
    if not model_path.is_file():
        raise RuntimeError(f"Model artifact was not found at {model_path}")
    if not metadata_path.is_file():
        raise RuntimeError(f"Model metadata was not found at {metadata_path}")

    metadata = json.loads(metadata_path.read_text())
    required_fields = {
        "model_name",
        "model_version",
        "training_timestamp",
        "git_commit",
        "experiment_run_id",
        "target_names",
    }
    missing_fields = required_fields - metadata.keys()
    if missing_fields:
        raise RuntimeError(f"Model metadata is missing: {', '.join(sorted(missing_fields))}")

    app.state.model = joblib.load(model_path)
    app.state.model_metadata = metadata
    app.state.target_names = metadata["target_names"]
    logger.info(
        "Loaded %s version %s (MLflow run %s) from %s",
        metadata["model_name"],
        metadata["model_version"],
        metadata["experiment_run_id"],
        model_path,
    )
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title="Iris Classification API",
    description="A small inference service used to demonstrate a GitOps MLOps pipeline.",
    version=settings.app_version,
    lifespan=lifespan,
)
app.mount("/metrics", make_asgi_app())


@app.get("/healthz", response_model=HealthResponse, tags=["operations"])
def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=hasattr(request.app.state, "model"))


@app.get("/readyz", response_model=HealthResponse, tags=["operations"])
def readiness(request: Request) -> HealthResponse:
    loaded = hasattr(request.app.state, "model")
    if not loaded:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return HealthResponse(status="ready", model_loaded=True)


@app.get("/version", response_model=VersionResponse, tags=["operations"])
def version(request: Request) -> VersionResponse:
    metadata = request.app.state.model_metadata
    return VersionResponse(
        application_version=settings.app_version,
        model_name=metadata["model_name"],
        model_version=metadata["model_version"],
        mlflow_run_id=metadata["experiment_run_id"],
    )


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
def predict(features: IrisFeatures, request: Request) -> PredictionResponse:
    model = request.app.state.model
    target_names: list[str] = request.app.state.target_names

    with PREDICTION_LATENCY.time():
        prediction = int(model.predict(features.as_model_input())[0])
        raw_probabilities = model.predict_proba(features.as_model_input())[0]

    class_name = target_names[prediction]
    PREDICTIONS.labels(predicted_class=class_name).inc()
    probabilities = {
        name: round(float(probability), 6)
        for name, probability in zip(target_names, raw_probabilities, strict=True)
    }
    return PredictionResponse(
        class_id=prediction,
        class_name=class_name,
        probabilities=probabilities,
        model_version=request.app.state.model_metadata["model_version"],
    )
