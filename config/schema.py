"""Configuration schema definitions using Pydantic for validation."""

from pydantic import BaseModel, EmailStr, Field, field_validator


class SMTPConfig(BaseModel):
    """SMTP server configuration."""

    server: str = Field(..., description="SMTP server hostname")
    port: int = Field(465, description="SMTP server port")
    use_tls: bool = Field(True, description="Use TLS/SSL encryption")
    username: str = Field(..., description="SMTP username/email")
    password: str = Field(..., description="SMTP password or app password")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class EmailTemplate(BaseModel):
    """Email template configuration."""

    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    attachments: list[str] = Field(default_factory=list, description="Default attachment paths")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file: str | None = Field(None, description="Log file path")
    console: bool = Field(True, description="Enable console logging")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Level must be one of: {valid_levels}")
        return v.upper()


class AppConfig(BaseModel):
    """Main application configuration."""

    smtp: SMTPConfig
    templates: dict[str, EmailTemplate] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    default_sender: EmailStr | None = Field(None, description="Default sender email")
    attachment_max_size: int = Field(
        25 * 1024 * 1024, description="Max attachment size in bytes (25MB)"
    )

    @field_validator("attachment_max_size")
    @classmethod
    def validate_attachment_size(cls, v):
        if v <= 0:
            raise ValueError("Attachment max size must be positive")
        return v


class ConfigDefaults:
    """Default configuration values."""

    SMTP_SERVERS = {
        "gmail": {"server": "smtp.gmail.com", "port": 465, "use_tls": True},
        "outlook": {"server": "smtp-mail.outlook.com", "port": 587, "use_tls": True},
        "yahoo": {"server": "smtp.mail.yahoo.com", "port": 465, "use_tls": True},
    }

    DEFAULT_CONFIG = {
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 465,
            "use_tls": True,
            "username": "",
            "password": "",
        },
        "logging": {"level": "INFO", "console": True},
        "attachment_max_size": 25 * 1024 * 1024,
    }
