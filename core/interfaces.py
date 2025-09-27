from abc import ABC, abstractmethod


class IEmailClient(ABC):
    """Interface for sending emails using any transport (SMTP, API, etc.)."""

    @abstractmethod
    def send(self, message) -> None:
        """Send an email message."""
        pass


class IAttachment(ABC):
    """Interface for handling attachments (PDF, DOCX, etc.)."""

    @abstractmethod
    def get_bytes(self) -> bytes:
        """Get attachment content as bytes."""
        pass

    @abstractmethod
    def get_filename(self) -> str:
        """Get attachment filename."""
        pass

    def get_mime_type(self) -> tuple[str, str]:
        """Get MIME type and subtype. Default implementation returns generic binary."""
        return "application", "octet-stream"

    def get_size(self) -> int:
        """Get attachment size in bytes. Default implementation calculates from bytes."""
        return len(self.get_bytes())
