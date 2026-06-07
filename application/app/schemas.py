from pydantic import BaseModel, Field


class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., ge=0, examples=[5.1])
    sepal_width: float = Field(..., ge=0, examples=[3.5])
    petal_length: float = Field(..., ge=0, examples=[1.4])
    petal_width: float = Field(..., ge=0, examples=[0.2])

    def as_model_input(self) -> list[list[float]]:
        return [[self.sepal_length, self.sepal_width, self.petal_length, self.petal_width]]


class PredictionResponse(BaseModel):
    class_id: int
    class_name: str
    probabilities: dict[str, float]
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class VersionResponse(BaseModel):
    application_version: str
    model_name: str
    model_version: str
    mlflow_run_id: str
