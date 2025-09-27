"""Tests for configuration management."""

from unittest.mock import patch

import pytest
import yaml

from config.manager import ConfigManager, ConfigurationError
from config.schema import AppConfig, ConfigDefaults, EmailTemplate, SMTPConfig


class TestAppConfig:
    """Test AppConfig validation."""

    def test_valid_config(self, sample_config_data):
        """Test creating valid configuration."""
        config = AppConfig(**sample_config_data)
        assert config.smtp.server == "smtp.test.com"
        assert config.smtp.port == 587
        assert config.default_sender == "test@example.com"

    def test_invalid_smtp_port(self, sample_config_data):
        """Test invalid SMTP port validation."""
        sample_config_data["smtp"]["port"] = 70000
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            AppConfig(**sample_config_data)

    def test_invalid_log_level(self, sample_config_data):
        """Test invalid log level validation."""
        sample_config_data["logging"]["level"] = "INVALID"
        with pytest.raises(ValueError, match="Level must be one of"):
            AppConfig(**sample_config_data)

    def test_invalid_attachment_size(self, sample_config_data):
        """Test invalid attachment size validation."""
        sample_config_data["attachment_max_size"] = -1
        with pytest.raises(ValueError, match="Attachment max size must be positive"):
            AppConfig(**sample_config_data)


class TestSMTPConfig:
    """Test SMTP configuration."""

    def test_valid_smtp_config(self):
        """Test valid SMTP configuration."""
        smtp_config = SMTPConfig(
            server="smtp.gmail.com",
            port=587,
            use_tls=True,
            username="test@example.com",
            password="password",
        )
        assert smtp_config.server == "smtp.gmail.com"
        assert smtp_config.port == 587
        assert smtp_config.use_tls is True

    def test_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError):
            SMTPConfig(
                server="smtp.gmail.com",
                port=0,
                username="test@example.com",
                password="password",
            )


class TestEmailTemplate:
    """Test email template."""

    def test_valid_template(self):
        """Test valid email template."""
        template = EmailTemplate(
            name="test",
            subject="Test Subject",
            body="Test Body",
            attachments=["file1.pdf", "file2.txt"],
        )
        assert template.name == "test"
        assert template.subject == "Test Subject"
        assert len(template.attachments) == 2


class TestConfigManager:
    """Test configuration manager."""

    def test_load_config_from_file(self, config_file):
        """Test loading configuration from file."""
        manager = ConfigManager(config_path=config_file)
        config = manager.load_config()

        assert isinstance(config, AppConfig)
        assert config.smtp.server == "smtp.test.com"

    def test_load_config_file_not_found(self, temp_dir):
        """Test loading configuration when file doesn't exist."""
        non_existent_path = temp_dir / "non_existent.yaml"
        manager = ConfigManager(config_path=non_existent_path)

        # Should load default config when file doesn't exist
        config = manager.load_config()
        assert isinstance(config, AppConfig)

    def test_save_config(self, temp_dir, sample_config):
        """Test saving configuration."""
        config_path = temp_dir / "test_config.yaml"
        manager = ConfigManager()

        saved_path = manager.save_config(sample_config, config_path)
        assert saved_path == config_path
        assert config_path.exists()

        # Verify saved content
        with open(config_path) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["smtp"]["server"] == "smtp.test.com"

    def test_create_default_config(self, temp_dir):
        """Test creating default configuration."""
        config_path = temp_dir / "default_config.yaml"
        manager = ConfigManager()

        created_path = manager.create_default_config(config_path)
        assert created_path == config_path
        assert config_path.exists()

    @patch.dict(
        "os.environ",
        {
            "EMAIL_SENDER_SMTP_SERVER": "env.smtp.com",
            "EMAIL_SENDER_SMTP_PORT": "465",
            "EMAIL_SENDER_SMTP_USERNAME": "env@example.com",
            "EMAIL_SENDER_DEFAULT_SENDER": "env@example.com",
        },
    )
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        manager = ConfigManager()
        config = manager.load_config()

        assert config.smtp.server == "env.smtp.com"
        assert config.smtp.port == 465
        assert config.smtp.username == "env@example.com"
        assert config.default_sender == "env@example.com"

    def test_invalid_yaml_file(self, temp_dir):
        """Test handling invalid YAML file."""
        invalid_config_path = temp_dir / "invalid.yaml"
        invalid_config_path.write_text("invalid: yaml: content: [")

        manager = ConfigManager(config_path=invalid_config_path)
        with pytest.raises(ConfigurationError):
            manager.load_config()

    def test_deep_merge(self):
        """Test deep merge functionality."""
        manager = ConfigManager()

        base = {
            "smtp": {"server": "base.com", "port": 587},
            "logging": {"level": "INFO"},
        }

        override = {"smtp": {"server": "override.com"}, "new_key": "new_value"}

        result = manager._deep_merge(base, override)

        assert result["smtp"]["server"] == "override.com"
        assert result["smtp"]["port"] == 587  # Preserved from base
        assert result["logging"]["level"] == "INFO"  # Preserved from base
        assert result["new_key"] == "new_value"  # Added from override


class TestConfigDefaults:
    """Test configuration defaults."""

    def test_smtp_servers(self):
        """Test predefined SMTP servers."""
        assert "gmail" in ConfigDefaults.SMTP_SERVERS
        assert "outlook" in ConfigDefaults.SMTP_SERVERS
        assert "yahoo" in ConfigDefaults.SMTP_SERVERS

        gmail_config = ConfigDefaults.SMTP_SERVERS["gmail"]
        assert gmail_config["server"] == "smtp.gmail.com"
        assert gmail_config["port"] == 465

    def test_default_config(self):
        """Test default configuration structure."""
        default_config = ConfigDefaults.DEFAULT_CONFIG
        assert "smtp" in default_config
        assert "logging" in default_config
        assert default_config["smtp"]["server"] == "smtp.gmail.com"
