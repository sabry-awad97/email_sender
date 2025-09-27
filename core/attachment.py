import mimetypes
from pathlib import Path
from typing import Tuple
from core.interfaces import IAttachment


class FileAttachment(IAttachment):
    """Generic file attachment implementation."""

    def __init__(self, filepath: str):
        self.path = Path(filepath)
        if not self.path.exists():
            raise FileNotFoundError(f"Attachment file not found: {filepath}")
        if not self.path.is_file():
            raise ValueError(f"Attachment path is not a file: {filepath}")

    def get_bytes(self) -> bytes:
        """Read and return file contents as bytes."""
        try:
            with open(self.path, "rb") as f:
                return f.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read attachment file {self.path}: {e}")

    def get_filename(self) -> str:
        """Return the filename without path."""
        return self.path.name

    def get_mime_type(self) -> Tuple[str, str]:
        """Get MIME type and subtype for the file."""
        mime_type, _ = mimetypes.guess_type(str(self.path))
        if mime_type:
            main_type, sub_type = mime_type.split("/", 1)
            return main_type, sub_type
        # Default to application/octet-stream for unknown types
        return "application", "octet-stream"

    def get_size(self) -> int:
        """Get file size in bytes."""
        return self.path.stat().st_size


# Backward compatibility alias
PDFAttachment = FileAttachment
