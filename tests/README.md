# Blueprint Tests

This directory contains tests for the Blueprint project.

## Structure

- `conftest.py`: Contains pytest fixtures and shared test configuration.
- `unit/`: Contains unit tests for specific modules.

## Running Tests

Run all tests using pytest:

```bash
# From project root
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_commit_generator.py
```

## Test Fixtures

The `conftest.py` file provides several fixtures that are useful for testing:

- `sample_git_diff`: A sample git diff for testing diff parsing functionality.
- `sample_ai_response`: A sample AI service response for testing commit message generation.

## Writing Tests

When adding new tests:

1. Use the pytest fixture system where appropriate.
2. Mock all external dependencies (subprocess, network calls, etc.).
3. Follow the Arrange-Act-Assert (AAA) pattern in test methods.
4. Add docstrings to test functions that explain what's being tested.

## Test Coverage

To generate a test coverage report:

```bash
# From project root
pytest --cov=blueprint tests/

# Generate HTML report
pytest --cov=blueprint --cov-report=html tests/
```

## Mocking Strategy

- Use `unittest.mock.patch` to mock dependencies like subprocess calls and AIService.
- When testing functions that call git commands, mock subprocess functions.
- For AI service interactions, mock the AIService class and its methods.
