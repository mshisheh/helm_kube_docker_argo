.PHONY: install train test lint run docker-build

install:
	python -m pip install -r requirements-dev.txt

train:
	python scripts/train_model.py

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn app.main:app --reload --port 8080

docker-build:
	docker build -t ml-api:local .
