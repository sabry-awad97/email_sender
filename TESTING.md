# Testing Guide

This document describes the comprehensive testing setup for the Email Sender CLI application.

## Test Structure

The test suite is organized into several categories:

```
tests/
├── __init__.py              # Test package
├── conftest.py              # Pytest fixtures and configuration
├── test_config.py           # Configuration management tests
├── test_core.py             # Core business logic tests
├── test_infrastructure.py   # Infrastructure component tests
├── test_cli.py              # CLI interface tests
└── test_integration.py      # End-to-end integration tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- High coverage of business logic

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- End-to-end workflows
- Real file system operations (with temp directories)
- More comprehensive but slower

### CLI Tests (`@pytest.mark.cli`)
- Test CLI commands and interfaces
- User interaction scenarios
- Command-line argument parsing
- Help text and error messages

### Slow Tests (`@pytest.mark.slow`)
- Tests that take longer to execute
- Network operations (mocked)
- Large data processing
- Can be excluded for quick development cycles

## Running Tests

### Using uv (Recommended)

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m "unit"                    # Unit tests only
uv run pytest -m "integration"             # Integration tests only
uv run pytest -m "cli"                     # CLI tests only
uv run pytest -m "not slow"                # Exclude slow tests

# Run with coverage
uv run pytest --cov=cli --cov=config --cov=core --cov=infrastructure --cov=models

# Run specific test file
uv run pytest tests/test_config.py -v

# Run specific test
uv run pytest tests/test_config.py::TestAppConfig::test_valid_config -v
```

### Using Make Commands

```bash
# Quick tests (unit tests, fast)
make test

# All test categories
make test-unit
make test-integration  
make test-cli
make test-fast
make test-all

# With coverage report
make test-coverage

# Code quality checks
make lint
make format
make check
```

### Using Test Runner Script

```bash
# Interactive test runner
python run_tests.py

# Specific options
python run_tests.py --type unit --verbose
python run_tests.py --coverage --html-report
python run_tests.py --parallel 4
```

## Test Configuration

### pytest.ini / pyproject.toml
- Test discovery patterns
- Marker definitions
- Coverage configuration
- Warning filters

### conftest.py Fixtures
- `temp_dir`: Temporary directory for file operations
- `sample_config`: Pre-configured AppConfig instance
- `config_file`: Temporary YAML config file
- `mock_smtp_client`: Mocked SMTP client
- `sample_attachment_file`: Test file for attachments
- `recipients_file`: Sample recipients list

## Writing Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestMyComponent:
    """Test MyComponent class."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        component = MyComponent()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.integration
    def test_integration_scenario(self, temp_dir):
        """Test integration with file system."""
        # Use fixtures for setup
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Test with real file operations
        result = component.process_file(test_file)
        assert result is not None
    
    @patch('module.external_dependency')
    def test_with_mocking(self, mock_dependency):
        """Test with mocked dependencies."""
        mock_dependency.return_value = "mocked_result"
        
        result = component.use_dependency()
        
        mock_dependency.assert_called_once()
        assert result == "mocked_result"
```

### Markers Usage

```python
@pytest.mark.unit
def test_unit_functionality():
    """Unit test - fast, isolated."""
    pass

@pytest.mark.integration  
def test_integration_workflow():
    """Integration test - slower, more comprehensive."""
    pass

@pytest.mark.cli
def test_cli_command():
    """CLI test - command-line interface."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test - can be excluded during development."""
    pass
```

## Coverage Reports

### Terminal Coverage
```bash
uv run pytest --cov=cli --cov=config --cov=core --cov=infrastructure --cov=models --cov-report=term-missing
```

### HTML Coverage Report
```bash
uv run pytest --cov=cli --cov=config --cov=core --cov=infrastructure --cov=models --cov-report=html:htmlcov
# Open htmlcov/index.html in browser
```

## Continuous Integration

The test suite is designed to work in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: uv sync --extra test

- name: Run tests
  run: uv run pytest --cov=cli --cov=config --cov=core --cov=infrastructure --cov=models

- name: Check code quality  
  run: |
    uv run ruff check .
    uv run ruff format --check .
```

## Test Data and Fixtures

### Temporary Files
- All file operations use `temp_dir` fixture
- Automatic cleanup after tests
- Cross-platform path handling

### Mock Objects
- SMTP client mocking for email tests
- Configuration manager mocking
- Rich console mocking to avoid output during tests

### Sample Data
- Valid/invalid configuration examples
- Email message templates
- Attachment files for testing

## Debugging Tests

### Verbose Output
```bash
uv run pytest -v -s  # Show print statements
```

### Specific Test Debugging
```bash
uv run pytest tests/test_config.py::TestAppConfig::test_valid_config -v -s --tb=long
```

### PDB Debugging
```python
def test_something():
    import pdb; pdb.set_trace()
    # Your test code
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (SMTP, file system when appropriate)
3. **Fixtures**: Use fixtures for common setup
4. **Markers**: Mark tests appropriately for selective running
5. **Coverage**: Aim for high test coverage but focus on critical paths
6. **Speed**: Keep unit tests fast, use integration tests for comprehensive scenarios
7. **Clarity**: Test names should clearly describe what is being tested
8. **Assertions**: Use descriptive assertion messages

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `uv sync --extra test` has been run
2. **Path Issues**: Use `temp_dir` fixture for file operations
3. **Mock Issues**: Ensure mocks are properly configured and reset
4. **Slow Tests**: Use markers to exclude slow tests during development

### Getting Help

```bash
# Show available pytest options
uv run pytest --help

# Show available markers
uv run pytest --markers

# Show test collection without running
uv run pytest --collect-only
```
