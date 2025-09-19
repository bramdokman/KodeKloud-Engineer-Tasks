.PHONY: test test-unit test-integration test-edge test-coverage clean lint type-check install help validate-all

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-edge     - Run edge case tests only"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run code linting"
	@echo "  type-check    - Run type checking"
	@echo "  validate-all  - Validate all task configurations"
	@echo "  clean         - Clean up generated files"

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest -v

# Run unit tests only
test-unit:
	pytest tests/test_config_validator.py -v -m unit

# Run integration tests only
test-integration:
	pytest tests/test_integration.py -v -m integration

# Run edge case tests only
test-edge:
	pytest tests/test_edge_cases.py -v

# Run tests with coverage
test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml

# Run linting
lint:
	flake8 src tests --max-line-length=127
	black --check src tests

# Run type checking
type-check:
	mypy src --ignore-missing-imports

# Validate all configurations
validate-all:
	@python -c "\
	from pathlib import Path; \
	from src.config_validator import validate_file; \
	import sys; \
	\
	categories = ['Kubernetes', 'Docker', 'Ansible', 'Git', 'Puppet']; \
	all_valid = True; \
	total_files = 0; \
	total_yaml_blocks = 0; \
	\
	for category in categories: \
		category_path = Path(category); \
		if category_path.exists(): \
			for task_file in category_path.glob('*.md'): \
				total_files += 1; \
				result = validate_file(task_file); \
				total_yaml_blocks += result['yaml_blocks']; \
				if not result['valid']: \
					print(f'❌ {task_file}: {len(result[\"errors\"])} errors'); \
					for error in result['errors']: \
						print(f'   - {error}'); \
					all_valid = False; \
				else: \
					print(f'✅ {task_file}: {result[\"yaml_blocks\"]} YAML blocks validated'); \
	\
	print(f'\\nSummary:'); \
	print(f'📁 Files processed: {total_files}'); \
	print(f'📄 YAML blocks validated: {total_yaml_blocks}'); \
	print(f'🎯 Overall status: {\"PASSED\" if all_valid else \"FAILED\"}'); \
	\
	sys.exit(0 if all_valid else 1)"

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Format code
format:
	black src tests

# Check code quality
quality: lint type-check

# Full CI pipeline
ci: install quality test-coverage validate-all