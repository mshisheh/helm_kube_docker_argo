.PHONY: test lint helm-lint terraform-fmt validate

test:
	cd application && pytest -q

lint:
	cd application && ruff check .

helm-lint:
	helm lint deployment/charts/ml-api -f deployment/environments/prod-values.yaml

terraform-fmt:
	terraform -chdir=infrastructure/terraform fmt -check -recursive

validate: lint test helm-lint terraform-fmt
