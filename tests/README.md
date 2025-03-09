# SCM CLI Tests

This directory contains the test suite for the Palo Alto Networks SCM CLI project. The tests ensure that the CLI functions correctly, handling inputs, commands, and API interactions properly.

## Test Files

- **test_cli.py**: Tests for the command-line interface functionality
- **test_config.py**: Tests for configuration loading and handling

## Running Tests

Tests can be run using pytest through Poetry:

```bash
# Run all tests
poetry run pytest

# Run a specific test file
poetry run pytest tests/test_config.py

# Run a specific test
poetry run pytest tests/test_config.py::test_load_oauth_credentials

# Run with verbose output
poetry run pytest -v
```

## Testing Approach

The tests use a combination of:

1. **Unit tests**: Testing individual functions and methods in isolation
2. **Mock objects**: Using `mock_sdk.py` to simulate SDK behavior without real API calls
3. **Fixtures**: Providing test data and environment setup

## Test Dependencies

The tests require:

- pytest
- unittest.mock (from the Python standard library)
- The mock_sdk module

## Adding New Tests

When adding new functionality to the CLI, corresponding tests should be added to ensure it works correctly. Consider:

1. Testing normal/expected operation
2. Testing edge cases
3. Testing error handling
4. Verifying proper interaction with the SDK
5. Verifying appropriate output to the user