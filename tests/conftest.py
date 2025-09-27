"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from config.manager import ConfigManager
from config.schema import AppConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "smtp": {
            "server": "smtp.test.com",
            "port": 587,
            "use_tls": True,
            "username": "test@example.com",
            "password": "test_password",
        },
        "default_sender": "test@example.com",
        "logging": {"level": "INFO", "console": True},
        "templates": {
            "test_template": {
                "name": "test_template",
                "subject": "Test Subject",
                "body": "Test Body",
                "attachments": [],
            }
        },
        "attachment_max_size": 25 * 1024 * 1024,
    }


@pytest.fixture
def sample_config(sample_config_data) -> AppConfig:
    """Create a sample AppConfig instance."""
    return AppConfig(**sample_config_data)


@pytest.fixture
def config_file(temp_dir, sample_config_data):
    """Create a temporary config file."""
    import yaml

    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_config_data, f)

    return config_path


@pytest.fixture
def mock_smtp_client():
    """Mock SMTP client for testing."""
    mock_client = Mock()
    mock_client.send = Mock()
    return mock_client


@pytest.fixture
def mock_config_manager(sample_config):
    """Mock configuration manager."""
    mock_manager = Mock(spec=ConfigManager)
    mock_manager.load_config.return_value = sample_config
    mock_manager.save_config.return_value = Path("/fake/path/config.yaml")
    mock_manager.config_file_path = Path("/fake/path/config.yaml")
    return mock_manager


@pytest.fixture
def sample_attachment_file(temp_dir):
    """Create a sample attachment file."""
    attachment_path = temp_dir / "test_attachment.txt"
    attachment_path.write_text("This is a test attachment.")
    return attachment_path


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock_logger = Mock()
    mock_logger.setup = Mock()
    mock_logger.info = Mock()
    mock_logger.error = Mock()
    mock_logger.success = Mock()
    mock_logger.warning = Mock()
    return mock_logger


@pytest.fixture
def recipients_file(temp_dir):
    """Create a sample recipients file."""
    recipients_path = temp_dir / "recipients.txt"
    recipients_path.write_text(
        "user1@example.com\nuser2@example.com\n# This is a comment\nuser3@example.com\n"
    )
    return recipients_path


@pytest.fixture(autouse=True)
def mock_rich_console():
    """Mock rich console to avoid output during tests."""
    with pytest.MonkeyPatch().context() as m:
        mock_console = Mock()
        m.setattr("rich.console.Console", lambda: mock_console)
        yield mock_console
