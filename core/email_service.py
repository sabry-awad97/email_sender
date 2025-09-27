from core.interfaces import IEmailClient
from models.email_message import EmailMessageModel


class EmailService:
    """High-level service that depends on abstractions (IEmailClient)."""

    def __init__(self, client: IEmailClient):
        self.client = client

    def send_email(self, message: EmailMessageModel):
        self.client.send(message)
