.PHONY: help install test test-unit test-integration test-edge coverage lint format clean

help:
	@echo "Available commands:"
	@echo "  make install         Install dependencies"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-edge      Run edge case tests only"
	@echo "  make coverage       Run tests with coverage report"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Format code with black"
	@echo "  make clean          Clean up generated files"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-edge:
	pytest tests/edge/ -v -m edge

coverage:
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml

lint:
	flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ --line-length=120

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/