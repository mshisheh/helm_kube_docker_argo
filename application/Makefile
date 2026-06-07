.PHONY: install train register promote export-production test lint run docker-build

install:
	python -m pip install -r requirements-dev.txt

train:
	python scripts/train_model.py

register:
	@test -n "$(RUN_ID)" || (echo "RUN_ID is required" && exit 1)
	python scripts/register_model.py register --run-id "$(RUN_ID)"

promote:
	@test -n "$(MODEL_VERSION)" || (echo "MODEL_VERSION is required" && exit 1)
	python scripts/register_model.py promote --version "$(MODEL_VERSION)"

export-production:
	python scripts/register_model.py export-production

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn app.main:app --reload --port 8080

docker-build:
	docker build -t ml-api:local .
