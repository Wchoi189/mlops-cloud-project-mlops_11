.PHONY: help install install-dev test lint format clean run-api run-mlflow docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean cache and artifacts"
	@echo "  run-api      Start FastAPI server"
	@echo "  run-mlflow   Start MLflow UI"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-mlflow:
	mlflow ui --host 0.0.0.0 --port 5000

docker-build:
	docker build -f docker/Dockerfile.api -t mlops-imdb-api .

docker-run:
	docker run -p 8000:8000 mlops-imdb-api
