# Testing Documentation

## Overview

This project implements comprehensive testing with industry-standard coverage (>90%). The test suite includes unit tests, integration tests, and edge case tests.

## Test Coverage Status

Current test coverage: **93.87%**

| Module | Coverage | Lines | Missing |
|--------|----------|-------|---------|
| `__init__.py` | 100% | 6 | 0 |
| `doc_validator.py` | 96.67% | 90 | 3 |
| `k8s_validator.py` | 86.29% | 175 | 24 |
| `task_parser.py` | 99.29% | 141 | 1 |
| `utils.py` | 96.81% | 94 | 3 |

## Test Structure

```
tests/
├── __init__.py
├── unit/                    # Unit tests for individual functions
│   ├── test_doc_validator.py
│   ├── test_k8s_validator.py
│   ├── test_task_parser.py
│   ├── test_utils.py
│   └── test_additional_coverage.py
├── integration/            # Integration tests
│   └── test_full_validation.py
└── edge/                   # Edge case tests
    └── test_edge_cases.py
```

## Running Tests

### Quick Test Run
```bash
# Run all tests
python run_tests.py

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/edge/ -v
```

### With Coverage
```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Using Tox
```bash
# Install tox
pip install tox

# Run tests in multiple Python versions
tox

# Run only coverage tests
tox -e coverage

# Run linting
tox -e lint
```

## Test Categories

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies
- Focus on edge cases and error handling
- Located in `tests/unit/`

### Integration Tests
- Test interaction between modules
- Validate end-to-end workflows
- Test file I/O and processing pipelines
- Located in `tests/integration/`

### Edge Case Tests
- Test boundary conditions
- Handle malformed inputs
- Test error recovery
- Security and path traversal tests
- Located in `tests/edge/`

## Coverage Requirements

- **Minimum Coverage**: 90%
- **Critical Modules**: 95%+ coverage
- **New Code**: Must have tests before merging
- **CI/CD**: Automatically enforced via GitHub Actions

## Writing Tests

### Test Naming Convention
```python
def test_<function_name>_<scenario>():
    """Test <description of what is being tested>."""
    pass
```

### Test Structure
```python
class TestModuleName:
    """Test suite for module_name."""

    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return {...}

    @pytest.mark.unit
    def test_function_normal_case(self, setup_data):
        """Test normal operation."""
        # Arrange
        input_data = setup_data

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value

    @pytest.mark.unit
    def test_function_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ExpectedException):
            function_under_test(invalid_input)
```

## Continuous Integration

The project uses GitHub Actions for CI/CD:

- **Test Matrix**: Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Coverage Enforcement**: Minimum 90% coverage required
- **Linting**: flake8 and mypy checks
- **Artifacts**: Coverage reports uploaded for each run

## Coverage Improvement

To improve coverage for specific modules:

1. Identify uncovered lines:
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

2. Write targeted tests for missing lines
3. Focus on:
   - Error handling paths
   - Edge cases
   - Complex conditional logic

## Common Test Patterns

### Mocking External Dependencies
```python
from unittest.mock import patch, Mock

@patch('module.external_function')
def test_with_mock(mock_external):
    mock_external.return_value = "mocked_value"
    result = function_under_test()
    assert result == expected
```

### Testing File Operations
```python
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    result = process_file(test_file)
    assert result == expected
```

### Testing Exceptions
```python
def test_exception_handling():
    with pytest.raises(ValueError) as exc_info:
        function_that_raises(bad_input)

    assert "expected message" in str(exc_info.value)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed with `pip install -e .`
2. **Missing Marks**: Add marks to pytest.ini or use `-m` flag
3. **Coverage Not Updated**: Clear `.coverage` file and re-run tests

### Debug Tips

- Use `pytest -vv` for verbose output
- Use `pytest --pdb` to drop into debugger on failure
- Use `pytest -k <pattern>` to run specific tests
- Use `pytest --tb=short` for shorter tracebacks