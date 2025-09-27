from abc import ABC, abstractmethod

class IEmailClient(ABC):
    """Interface for sending emails using any transport (SMTP, API, etc.)."""
    @abstractmethod
    def send(self, message) -> None:
        pass

class IAttachment(ABC):
    """Interface for handling attachments (PDF, DOCX, etc.)."""
    @abstractmethod
    def get_bytes(self) -> bytes:
        pass

    @abstractmethod
    def get_filename(self) -> str:
        pass
