"""Tests for core business logic."""

from unittest.mock import Mock, patch

import pytest

from core.attachment import FileAttachment
from core.email_service import EmailService
from core.interfaces import IAttachment, IEmailClient
from models.email_message import EmailMessageModel


class TestEmailService:
    """Test EmailService class."""

    def test_send_email(self, mock_smtp_client):
        """Test sending email through service."""
        service = EmailService(mock_smtp_client)

        message = EmailMessageModel(
            sender="test@example.com",
            receiver="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[],
        )

        service.send_email(message)
        mock_smtp_client.send.assert_called_once_with(message)

    def test_dependency_injection(self):
        """Test that EmailService accepts any IEmailClient implementation."""
        mock_client = Mock(spec=IEmailClient)
        service = EmailService(mock_client)

        assert service.client == mock_client


class TestFileAttachment:
    """Test FileAttachment class."""

    def test_valid_attachment(self, sample_attachment_file):
        """Test creating attachment from valid file."""
        attachment = FileAttachment(str(sample_attachment_file))

        assert attachment.get_filename() == "test_attachment.txt"
        assert attachment.get_bytes() == b"This is a test attachment."
        assert attachment.get_size() == len("This is a test attachment.")

    def test_file_not_found(self):
        """Test creating attachment from non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileAttachment("non_existent_file.txt")

    def test_directory_path(self, temp_dir):
        """Test creating attachment from directory path."""
        with pytest.raises(ValueError, match="Attachment path is not a file"):
            FileAttachment(str(temp_dir))

    def test_mime_type_detection(self, temp_dir):
        """Test MIME type detection for different file types."""
        # Test PDF file
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        pdf_attachment = FileAttachment(str(pdf_file))
        main_type, sub_type = pdf_attachment.get_mime_type()
        assert main_type == "application"
        assert sub_type == "pdf"

        # Test text file
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("text content")
        txt_attachment = FileAttachment(str(txt_file))
        main_type, sub_type = txt_attachment.get_mime_type()
        assert main_type == "text"
        assert sub_type == "plain"

    def test_unknown_mime_type(self, temp_dir):
        """Test unknown file extension defaults."""
        unknown_file = temp_dir / "test.unknown_extension"
        unknown_file.write_bytes(b"unknown content")
        attachment = FileAttachment(str(unknown_file))

        main_type, sub_type = attachment.get_mime_type()
        assert main_type == "application"
        assert sub_type == "octet-stream"

    def test_file_read_error(self, temp_dir):
        """Test handling file read errors."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        attachment = FileAttachment(str(test_file))

        # Mock file read to raise an error
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(RuntimeError, match="Failed to read attachment file"):
                attachment.get_bytes()

    def test_backward_compatibility(self, sample_attachment_file):
        """Test PDFAttachment alias for backward compatibility."""
        from core.attachment import PDFAttachment

        # PDFAttachment should be an alias for FileAttachment
        assert PDFAttachment == FileAttachment

        # Should work the same way
        attachment = PDFAttachment(str(sample_attachment_file))
        assert attachment.get_filename() == "test_attachment.txt"


class TestInterfaces:
    """Test abstract interfaces."""

    def test_iemail_client_interface(self):
        """Test IEmailClient interface."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IEmailClient()

    def test_iattachment_interface(self):
        """Test IAttachment interface."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IAttachment()

    def test_iattachment_default_methods(self):
        """Test IAttachment default method implementations."""

        class TestAttachment(IAttachment):
            def get_bytes(self) -> bytes:
                return b"test content"

            def get_filename(self) -> str:
                return "test.txt"

        attachment = TestAttachment()

        # Test default MIME type
        main_type, sub_type = attachment.get_mime_type()
        assert main_type == "application"
        assert sub_type == "octet-stream"

        # Test default size calculation
        assert attachment.get_size() == len(b"test content")


class TestEmailMessageModel:
    """Test EmailMessageModel data class."""

    def test_create_message(self):
        """Test creating email message."""
        message = EmailMessageModel(
            sender="sender@example.com",
            receiver="receiver@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        assert message.sender == "sender@example.com"
        assert message.receiver == "receiver@example.com"
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.attachments == []

    def test_message_with_attachments(self, sample_attachment_file):
        """Test creating message with attachments."""
        attachment = FileAttachment(str(sample_attachment_file))

        message = EmailMessageModel(
            sender="sender@example.com",
            receiver="receiver@example.com",
            subject="Test Subject",
            body="Test Body",
            attachments=[attachment],
        )

        assert len(message.attachments) == 1
        assert message.attachments[0] == attachment

    def test_message_dataclass_features(self):
        """Test dataclass features like equality."""
        message1 = EmailMessageModel(
            sender="sender@example.com",
            receiver="receiver@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        message2 = EmailMessageModel(
            sender="sender@example.com",
            receiver="receiver@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        assert message1 == message2
