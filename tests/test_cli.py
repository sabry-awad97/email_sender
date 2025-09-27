"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from cli.commands.config import config_command
from cli.commands.template import template_command
from cli.main import cli


class TestMainCLI:
    """Test main CLI interface."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Email Sender CLI" in result.output
        assert "send" in result.output
        assert "config" in result.output
        assert "template" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    @patch("cli.main.ConfigManager")
    def test_cli_with_config_file(self, mock_config_manager, sample_config):
        """Test CLI with custom config file."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("test_config.yaml").touch()
            result = runner.invoke(cli, ["--config", "test_config.yaml", "version"])

            assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_cli_verbose_mode(self, mock_config_manager, sample_config):
        """Test CLI verbose mode."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "version"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_cli_quiet_mode(self, mock_config_manager, sample_config):
        """Test CLI quiet mode."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["--quiet", "version"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_cli_config_error_handling(self, mock_config_manager):
        """Test CLI handling of configuration errors."""
        from config.manager import ConfigurationError

        mock_manager = Mock()
        mock_manager.load_config.side_effect = ConfigurationError("Config error")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        # Should not fail, but should show warning
        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_status_command(self, mock_config_manager, sample_config):
        """Test status command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0


class TestSendCommand:
    """Test send commands."""

    @patch("cli.commands.send.EmailService")
    @patch("cli.commands.send.SMTPClient")
    @patch("cli.main.ConfigManager")
    def test_send_single_basic(
        self, mock_config_manager, mock_smtp_client, mock_email_service, sample_config
    ):
        """Test basic single email sending."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        mock_client = Mock()
        mock_smtp_client.return_value = mock_client

        mock_service = Mock()
        mock_email_service.return_value = mock_service

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "send",
                "single",
                "--to",
                "test@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test Body",
            ],
        )

        assert result.exit_code == 0
        mock_service.send_email.assert_called_once()

    @patch("cli.main.ConfigManager")
    def test_send_single_no_config(self, mock_config_manager):
        """Test send command without configuration."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = None
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "send",
                "single",
                "--to",
                "test@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test Body",
            ],
        )

        assert result.exit_code == 1

    @patch("cli.commands.send.EmailService")
    @patch("cli.commands.send.SMTPClient")
    @patch("cli.main.ConfigManager")
    def test_send_single_with_attachment(
        self,
        mock_config_manager,
        mock_smtp_client,
        mock_email_service,
        sample_config,
        sample_attachment_file,
    ):
        """Test sending email with attachment."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        mock_client = Mock()
        mock_smtp_client.return_value = mock_client

        mock_service = Mock()
        mock_email_service.return_value = mock_service

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "send",
                "single",
                "--to",
                "test@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test Body",
                "--attach",
                str(sample_attachment_file),
            ],
        )

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_send_single_dry_run(self, mock_config_manager, sample_config):
        """Test dry run mode."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "send",
                "single",
                "--to",
                "test@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test Body",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_send_bulk(self, mock_config_manager, sample_config, recipients_file):
        """Test bulk email sending."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        with patch("cli.commands.send.Confirm.ask", return_value=False):  # Cancel bulk send
            result = runner.invoke(
                cli,
                [
                    "send",
                    "bulk",
                    "--recipients-file",
                    str(recipients_file),
                    "--subject",
                    "Test Subject",
                    "--body",
                    "Test Body",
                ],
            )

        assert result.exit_code == 0


class TestConfigCommand:
    """Test config commands."""

    def test_config_help(self):
        """Test config command help."""
        runner = CliRunner()
        result = runner.invoke(config_command, ["--help"])

        assert result.exit_code == 0
        assert "init" in result.output
        assert "show" in result.output
        assert "set" in result.output

    @patch("cli.commands.config.ConfigManager")
    def test_config_init(self, mock_config_manager):
        """Test config initialization."""
        mock_manager = Mock()
        mock_manager.save_config.return_value = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["config", "init", "--path", "test_config.yaml"])

            assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_config_show(self, mock_config_manager, sample_config):
        """Test config show command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_config_show_yaml_format(self, mock_config_manager, sample_config):
        """Test config show in YAML format."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show", "--format", "yaml"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_config_set(self, mock_config_manager, sample_config):
        """Test config set command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_manager.save_config.return_value = Path("/fake/config.yaml")
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "set", "smtp.server", "new.smtp.com"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_config_validate(self, mock_config_manager, sample_config):
        """Test config validation."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        with patch("smtplib.SMTP_SSL") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = runner.invoke(cli, ["config", "validate"])

            assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_config_path(self, mock_config_manager):
        """Test config path command."""
        mock_manager = Mock()
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "path"])

        assert result.exit_code == 0


class TestTemplateCommand:
    """Test template commands."""

    def test_template_help(self):
        """Test template command help."""
        runner = CliRunner()
        result = runner.invoke(template_command, ["--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output
        assert "show" in result.output

    @patch("cli.main.ConfigManager")
    def test_template_list(self, mock_config_manager, sample_config):
        """Test template list command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "list"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_template_show(self, mock_config_manager, sample_config):
        """Test template show command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "show", "test_template"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_template_create(self, mock_config_manager, sample_config):
        """Test template create command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_manager.save_config.return_value = Path("/fake/config.yaml")
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "template",
                "create",
                "new_template",
                "--subject",
                "New Subject",
                "--body",
                "New Body",
            ],
        )

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_template_delete(self, mock_config_manager, sample_config):
        """Test template delete command."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_manager.save_config.return_value = Path("/fake/config.yaml")
        mock_manager.config_file_path = Path("/fake/config.yaml")
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        with patch("cli.commands.template.Confirm.ask", return_value=True):
            result = runner.invoke(cli, ["template", "delete", "test_template"])

        assert result.exit_code == 0

    @patch("cli.main.ConfigManager")
    def test_template_not_found(self, mock_config_manager, sample_config):
        """Test template commands with non-existent template."""
        mock_manager = Mock()
        mock_manager.load_config.return_value = sample_config
        mock_config_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "show", "non_existent"])

        assert result.exit_code == 1
