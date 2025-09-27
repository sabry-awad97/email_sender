"""Configuration manager for handling YAML config files and environment variables."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .schema import AppConfig, ConfigDefaults


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class ConfigManager:
    """Manages application configuration from files and environment variables."""

    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".email-sender" / "config.yaml",
        Path.cwd() / "config.yaml",
        Path.cwd() / ".email-sender.yaml",
    ]

    ENV_PREFIX = "EMAIL_SENDER_"

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Explicit path to configuration file
        """
        self.config_path = config_path
        self._config: AppConfig | None = None

    def load_config(self) -> AppConfig:
        """Load configuration from file and environment variables.

        Returns:
            Validated application configuration

        Raises:
            ConfigurationError: If configuration is invalid or required values are missing
        """
        if self._config is not None:
            return self._config

        # Start with default configuration
        config_data = ConfigDefaults.DEFAULT_CONFIG.copy()

        # Load from file if available
        config_file = self._find_config_file()
        if config_file:
            try:
                with open(config_file, encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
                config_data = self._deep_merge(config_data, file_config)
            except (OSError, yaml.YAMLError) as e:
                raise ConfigurationError(f"Failed to load config file {config_file}: {e}") from e

        # Override with environment variables
        env_config = self._load_from_env()
        config_data = self._deep_merge(config_data, env_config)

        # Validate configuration
        try:
            self._config = AppConfig(**config_data)
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

        return self._config

    def save_config(self, config: AppConfig, path: Path | None = None) -> Path:
        """Save configuration to file.

        Args:
            config: Configuration to save
            path: Path to save to (defaults to first default path)

        Returns:
            Path where configuration was saved
        """
        if path is None:
            path = self.DEFAULT_CONFIG_PATHS[0]

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        config_dict = config.model_dump()

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except OSError as e:
            raise ConfigurationError(f"Failed to save config to {path}: {e}") from e

        return path

    def create_default_config(self, path: Path | None = None) -> Path:
        """Create a default configuration file with placeholders.

        Args:
            path: Path to create config file at

        Returns:
            Path where configuration was created
        """
        if path is None:
            path = self.DEFAULT_CONFIG_PATHS[0]

        # Create config with placeholder values
        config_data = {
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 465,
                "use_tls": True,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
            },
            "default_sender": "your-email@gmail.com",
            "logging": {"level": "INFO", "console": True},
            "templates": {
                "default": {
                    "name": "default",
                    "subject": "Email from CLI",
                    "body": "This email was sent using the email-sender CLI tool.",
                    "attachments": [],
                }
            },
        }

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        except OSError as e:
            raise ConfigurationError(f"Failed to create config file at {path}: {e}") from e

        return path

    def _find_config_file(self) -> Path | None:
        """Find the first available configuration file."""
        if self.config_path:
            return self.config_path if self.config_path.exists() else None

        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path

        return None

    def _load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # SMTP configuration
        smtp_config = {}
        if server := os.getenv(f"{self.ENV_PREFIX}SMTP_SERVER"):
            smtp_config["server"] = server
        if port := os.getenv(f"{self.ENV_PREFIX}SMTP_PORT"):
            try:
                smtp_config["port"] = int(port)
            except ValueError:
                pass
        if username := os.getenv(f"{self.ENV_PREFIX}SMTP_USERNAME"):
            smtp_config["username"] = username
        if password := os.getenv(f"{self.ENV_PREFIX}SMTP_PASSWORD"):
            smtp_config["password"] = password
        if use_tls := os.getenv(f"{self.ENV_PREFIX}SMTP_USE_TLS"):
            smtp_config["use_tls"] = use_tls.lower() in ("true", "1", "yes")

        if smtp_config:
            env_config["smtp"] = smtp_config

        # Other configuration
        if sender := os.getenv(f"{self.ENV_PREFIX}DEFAULT_SENDER"):
            env_config["default_sender"] = sender

        if log_level := os.getenv(f"{self.ENV_PREFIX}LOG_LEVEL"):
            env_config["logging"] = {"level": log_level.upper()}

        return env_config

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @property
    def config_file_path(self) -> Path | None:
        """Get the path to the currently loaded config file."""
        return self._find_config_file()

    def reset(self):
        """Reset cached configuration."""
        self._config = None
