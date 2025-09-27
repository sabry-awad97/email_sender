"""Integration tests for the email sender CLI."""

from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from config.manager import ConfigManager
from config.schema import AppConfig


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_email_workflow(self, temp_dir):
        """Test complete workflow from config creation to email sending."""
        runner = CliRunner()

        # Step 1: Create configuration
        config_path = temp_dir / "test_config.yaml"
        result = runner.invoke(cli, ["config", "init", "--path", str(config_path)])
        assert result.exit_code == 0
        assert config_path.exists()

        # Step 2: Update configuration with valid SMTP settings
        result = runner.invoke(
            cli,
            ["--config", str(config_path), "config", "set", "smtp.username", "test@example.com"],
        )
        assert result.exit_code == 0

        # Step 3: Create a template
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_path),
                "template",
                "create",
                "test_template",
                "--subject",
                "Test Subject",
                "--body",
                "Test Body",
            ],
        )
        assert result.exit_code == 0

        # Step 4: List templates to verify creation
        result = runner.invoke(cli, ["--config", str(config_path), "template", "list"])
        assert result.exit_code == 0

        # Step 5: Send email in dry-run mode
        with patch("cli.commands.send.EmailService"), patch("cli.commands.send.SMTPClient"):
            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(config_path),
                    "send",
                    "single",
                    "--to",
                    "recipient@example.com",
                    "--template",
                    "test_template",
                    "--dry-run",
                ],
            )
            assert result.exit_code == 0

    def test_bulk_email_workflow(self, temp_dir):
        """Test bulk email sending workflow."""
        runner = CliRunner()

        # Create config
        config_path = temp_dir / "config.yaml"
        config_data = {
            "smtp": {
                "server": "smtp.test.com",
                "port": 587,
                "use_tls": True,
                "username": "test@example.com",
                "password": "password",
            },
            "default_sender": "test@example.com",
            "logging": {"level": "INFO", "console": True},
        }

        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Create recipients file
        recipients_file = temp_dir / "recipients.txt"
        recipients_file.write_text("user1@example.com\nuser2@example.com\nuser3@example.com\n")

        # Create template
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_path),
                "template",
                "create",
                "newsletter",
                "--subject",
                "Monthly Newsletter",
                "--body",
                "Newsletter content here",
            ],
        )
        assert result.exit_code == 0

        # Send bulk emails in dry-run mode
        with patch("cli.commands.send.Confirm.ask", return_value=True):
            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(config_path),
                    "send",
                    "bulk",
                    "--recipients-file",
                    str(recipients_file),
                    "--template",
                    "newsletter",
                    "--dry-run",
                ],
            )
            assert result.exit_code == 0

    def test_configuration_validation_workflow(self, temp_dir):
        """Test configuration validation workflow."""
        runner = CliRunner()

        # Create invalid config
        config_path = temp_dir / "invalid_config.yaml"
        invalid_config = {
            "smtp": {
                "server": "invalid.server.com",
                "port": 99999,  # Invalid port
                "username": "test@example.com",
                "password": "password",
            }
        }

        with open(config_path, "w") as f:
            yaml.dump(invalid_config, f)

        # Try to validate - should fail
        result = runner.invoke(cli, ["--config", str(config_path), "config", "validate"])
        # Should exit with error due to invalid port during config loading
        assert result.exit_code != 0

    def test_template_management_workflow(self, temp_dir):
        """Test complete template management workflow."""
        runner = CliRunner()

        # Create config
        config_path = temp_dir / "config.yaml"
        result = runner.invoke(cli, ["config", "init", "--path", str(config_path)])
        assert result.exit_code == 0

        # Create multiple templates
        templates = [
            ("welcome", "Welcome!", "Welcome to our service"),
            ("newsletter", "Newsletter", "Monthly newsletter content"),
            ("reminder", "Reminder", "This is a reminder"),
        ]

        for name, subject, body in templates:
            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(config_path),
                    "template",
                    "create",
                    name,
                    "--subject",
                    subject,
                    "--body",
                    body,
                ],
            )
            assert result.exit_code == 0

        # List all templates
        result = runner.invoke(cli, ["--config", str(config_path), "template", "list"])
        assert result.exit_code == 0

        # Show specific template
        result = runner.invoke(cli, ["--config", str(config_path), "template", "show", "welcome"])
        assert result.exit_code == 0

        # Edit template
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_path),
                "template",
                "edit",
                "welcome",
                "--subject",
                "Updated Welcome!",
            ],
        )
        assert result.exit_code == 0

        # Copy template
        result = runner.invoke(
            cli, ["--config", str(config_path), "template", "copy", "welcome", "welcome_v2"]
        )
        assert result.exit_code == 0

        # Delete template
        with patch("cli.commands.template.Confirm.ask", return_value=True):
            result = runner.invoke(
                cli, ["--config", str(config_path), "template", "delete", "reminder"]
            )
            assert result.exit_code == 0


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration system integration."""

    def test_config_file_precedence(self, temp_dir):
        """Test configuration file precedence and merging."""
        _runner = CliRunner()

        # Create base config
        config_path = temp_dir / "config.yaml"
        base_config = {
            "smtp": {
                "server": "base.smtp.com",
                "port": 587,
                "username": "base@example.com",
                "password": "base_password",
            },
            "logging": {"level": "INFO"},
        }

        with open(config_path, "w") as f:
            yaml.dump(base_config, f)

        # Test environment variable override
        with patch.dict(
            "os.environ",
            {"EMAIL_SENDER_SMTP_SERVER": "env.smtp.com", "EMAIL_SENDER_SMTP_PORT": "465"},
        ):
            # Load config and verify environment variables take precedence
            manager = ConfigManager(config_path=config_path)
            config = manager.load_config()

            assert config.smtp.server == "env.smtp.com"
            assert config.smtp.port == 465
            assert config.smtp.username == "base@example.com"  # From file

    def test_config_validation_integration(self, temp_dir):
        """Test configuration validation with real ConfigManager."""
        # Create valid config
        config_path = temp_dir / "valid_config.yaml"
        valid_config = {
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 465,
                "use_tls": True,
                "username": "test@gmail.com",
                "password": "app_password",
            },
            "default_sender": "test@gmail.com",
            "logging": {"level": "INFO", "console": True},
            "attachment_max_size": 25 * 1024 * 1024,
        }

        with open(config_path, "w") as f:
            yaml.dump(valid_config, f)

        # Load and validate
        manager = ConfigManager(config_path=config_path)
        config = manager.load_config()

        assert isinstance(config, AppConfig)
        assert config.smtp.server == "smtp.gmail.com"
        assert config.attachment_max_size == 25 * 1024 * 1024


@pytest.mark.integration
@pytest.mark.slow
class TestSMTPIntegration:
    """Test SMTP integration (mocked for safety)."""

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    def test_smtp_connection_integration(self, mock_smtp_ssl, sample_config):
        """Test SMTP connection with real client."""
        from infrastructure.smtp_client import SMTPClient
        from models.email_message import EmailMessageModel

        # Setup mock
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        # Create client and send email
        client = SMTPClient(
            smtp_server=sample_config.smtp.server,
            port=sample_config.smtp.port,
            username=sample_config.smtp.username,
            password=sample_config.smtp.password,
            use_tls=sample_config.smtp.use_tls,
        )

        message = EmailMessageModel(
            sender=sample_config.smtp.username,
            receiver="test@example.com",
            subject="Integration Test",
            body="This is an integration test email.",
            attachments=[],
        )

        client.send(message)

        # Verify SMTP operations
        mock_server.login.assert_called_once_with(
            sample_config.smtp.username, sample_config.smtp.password
        )
        mock_server.send_message.assert_called_once()

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    def test_attachment_integration(self, mock_smtp_ssl, sample_config, sample_attachment_file):
        """Test email with attachment integration."""
        from core.attachment import FileAttachment
        from infrastructure.smtp_client import SMTPClient
        from models.email_message import EmailMessageModel

        # Setup mock
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        # Create client
        client = SMTPClient(
            smtp_server=sample_config.smtp.server,
            port=sample_config.smtp.port,
            username=sample_config.smtp.username,
            password=sample_config.smtp.password,
        )

        # Create message with attachment
        attachment = FileAttachment(str(sample_attachment_file))
        message = EmailMessageModel(
            sender=sample_config.smtp.username,
            receiver="test@example.com",
            subject="Integration Test with Attachment",
            body="This email has an attachment.",
            attachments=[attachment],
        )

        client.send(message)

        # Verify operations
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across the system."""

    def test_missing_config_file_handling(self):
        """Test handling of missing configuration file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Try to use non-existent config file
            result = runner.invoke(cli, ["--config", "non_existent.yaml", "status"])

            # Should not crash, but may show error (exit code 2 is acceptable for missing config)
            assert result.exit_code in [0, 2]

    def test_invalid_attachment_handling(self, temp_dir):
        """Test handling of invalid attachment files."""
        runner = CliRunner()

        # Create config
        config_path = temp_dir / "config.yaml"
        result = runner.invoke(cli, ["config", "init", "--path", str(config_path)])
        assert result.exit_code == 0

        # Try to send email with non-existent attachment
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_path),
                "send",
                "single",
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--attach",
                "non_existent_file.pdf",
            ],
        )

        # Should fail gracefully (exit code 2 is acceptable for CLI errors)
        assert result.exit_code in [1, 2]

    def test_invalid_recipients_file_handling(self, temp_dir):
        """Test handling of invalid recipients file."""
        runner = CliRunner()

        # Create config
        config_path = temp_dir / "config.yaml"
        result = runner.invoke(cli, ["config", "init", "--path", str(config_path)])
        assert result.exit_code == 0

        # Try bulk send with non-existent recipients file
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_path),
                "send",
                "bulk",
                "--recipients-file",
                "non_existent_recipients.txt",
                "--subject",
                "Test",
                "--body",
                "Test",
            ],
        )

        # Should fail gracefully (exit code 2 is acceptable for CLI errors)
        assert result.exit_code in [1, 2]
