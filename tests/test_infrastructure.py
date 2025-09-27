"""Tests for infrastructure components."""

import smtplib
from email.message import EmailMessage
from unittest.mock import Mock, patch

import pytest

from core.attachment import FileAttachment
from infrastructure.logger import Logger
from infrastructure.smtp_client import SMTPClient, SMTPClientError
from models.email_message import EmailMessageModel


class TestSMTPClient:
    """Test SMTP client implementation."""

    def test_smtp_client_initialization(self):
        """Test SMTP client initialization."""
        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=587,
            username="test@example.com",
            password="password",
            use_tls=True,
        )

        assert client.smtp_server == "smtp.test.com"
        assert client.port == 587
        assert client.username == "test@example.com"
        assert client.password == "password"
        assert client.use_tls is True

    def test_smtp_client_default_tls(self):
        """Test SMTP client with default TLS setting."""
        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=587,
            username="test@example.com",
            password="password",
        )

        assert client.use_tls is True  # Default should be True

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    @patch("infrastructure.smtp_client.Logger")
    def test_send_email_success_tls(self, mock_logger, mock_smtp_ssl):
        """Test successful email sending with TLS."""
        # Setup mocks
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=465,
            username="test@example.com",
            password="password",
            use_tls=True,
        )

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[],
        )

        client.send(message)

        # Verify SMTP operations
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
        mock_logger.success.assert_called_once()

    @patch("infrastructure.smtp_client.smtplib.SMTP")
    @patch("infrastructure.smtp_client.Logger")
    def test_send_email_success_no_tls(self, mock_logger, mock_smtp):
        """Test successful email sending without TLS."""
        # Setup mocks
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=587,
            username="test@example.com",
            password="password",
            use_tls=False,
        )

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[],
        )

        client.send(message)

        # Verify SMTP operations
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    @patch("infrastructure.smtp_client.Logger")
    def test_send_email_with_attachment(self, mock_logger, mock_smtp_ssl, sample_attachment_file):
        """Test sending email with attachment."""
        # Setup mocks
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=465,
            username="test@example.com",
            password="password",
        )

        attachment = FileAttachment(str(sample_attachment_file))
        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[attachment],
        )

        client.send(message)

        # Verify attachment was processed
        mock_logger.info.assert_any_call(
            f"Added attachment: {attachment.get_filename()} ({attachment.get_size()} bytes)"
        )

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    @patch("infrastructure.smtp_client.Logger")
    def test_send_email_smtp_auth_error(self, mock_logger, mock_smtp_ssl):
        """Test SMTP authentication error handling."""
        # Setup mocks
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=465,
            username="test@example.com",
            password="wrong_password",
        )

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[],
        )

        with pytest.raises(SMTPClientError, match="Failed to send email"):
            client.send(message)

        mock_logger.error.assert_called()

    @patch("infrastructure.smtp_client.smtplib.SMTP_SSL")
    @patch("infrastructure.smtp_client.Logger")
    def test_send_email_connection_error(self, mock_logger, mock_smtp_ssl):
        """Test SMTP connection error handling."""
        # Setup mocks to raise connection error
        mock_smtp_ssl.side_effect = ConnectionRefusedError("Connection refused")

        client = SMTPClient(
            smtp_server="invalid.server.com",
            port=465,
            username="test@example.com",
            password="password",
        )

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[],
        )

        with pytest.raises(SMTPClientError, match="Failed to send email"):
            client.send(message)

    def test_build_email_message(self, sample_attachment_file):
        """Test email message building."""
        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=465,
            username="test@example.com",
            password="password",
        )

        attachment = FileAttachment(str(sample_attachment_file))
        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[attachment],
        )

        email_message = client._build_email_message(message)

        assert isinstance(email_message, EmailMessage)
        assert email_message["From"] == "test@example.com"
        assert email_message["To"] == "recipient@example.com"
        assert email_message["Subject"] == "Test Subject"

    @patch("infrastructure.smtp_client.Logger")
    def test_attachment_error_handling(self, mock_logger, temp_dir):
        """Test attachment error handling."""
        client = SMTPClient(
            smtp_server="smtp.test.com",
            port=465,
            username="test@example.com",
            password="password",
        )

        # Create a mock attachment that raises an error
        mock_attachment = Mock()
        mock_attachment.get_filename.return_value = "error_file.txt"
        mock_attachment.get_mime_type.side_effect = Exception("File read error")

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[mock_attachment],
        )

        with pytest.raises(Exception, match="File read error"):
            client._build_email_message(message)


class TestLogger:
    """Test Logger class."""

    def test_logger_setup(self):
        """Test logger setup."""
        Logger._logger = None  # Reset logger state
        Logger.setup(level="DEBUG", console=True)
        logger = Logger.get_logger()

        assert logger.name == "email-sender"
        assert logger.level == 10  # DEBUG level

    def test_logger_methods(self):
        """Test logger methods."""
        Logger._logger = None  # Reset logger state
        Logger.setup()

        # These should not raise exceptions
        Logger.debug("Debug message")
        Logger.info("Info message")
        Logger.warning("Warning message")
        Logger.error("Error message")
        Logger.critical("Critical message")
        Logger.success("Success message")

    @patch("infrastructure.logger.logging.FileHandler")
    def test_logger_file_output(self, mock_file_handler):
        """Test logger file output configuration."""
        Logger._logger = None  # Reset logger
        Logger.setup(level="INFO", log_file="test.log")

        mock_file_handler.assert_called_once()

    def test_logger_singleton_behavior(self):
        """Test logger singleton behavior."""
        Logger._logger = None  # Reset logger

        logger1 = Logger.get_logger()
        logger2 = Logger.get_logger()

        assert logger1 is logger2

    def test_logger_exception_method(self):
        """Test logger exception method."""
        Logger.setup()

        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise an exception
            Logger.exception("Exception occurred")

    def test_logger_creates_log_directory(self, temp_dir):
        """Test that logger creates log directory if it doesn't exist."""
        Logger._logger = None  # Reset logger
        log_file = temp_dir / "logs" / "test.log"
        Logger.setup(log_file=str(log_file))

        # Directory should be created
        assert log_file.parent.exists()

        # Clean up logger handlers to release file
        if Logger._logger:
            for handler in Logger._logger.handlers[:]:
                handler.close()
                Logger._logger.removeHandler(handler)
        Logger._logger = None
