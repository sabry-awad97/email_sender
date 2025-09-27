from core.interfaces import IAttachment

class PDFAttachment(IAttachment):
    """Concrete implementation for PDF attachments."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    def get_bytes(self) -> bytes:
        with open(self.filepath, "rb") as f:
            return f.read()

    def get_filename(self) -> str:
        return self.filepath.split("/")[-1]
