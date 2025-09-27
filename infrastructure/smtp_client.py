import smtplib, ssl
from email.message import EmailMessage as PyEmailMessage
from core.interfaces import IEmailClient
from infrastructure.logger import Logger

class SMTPClient(IEmailClient):
    """Concrete SMTP implementation of IEmailClient."""

    def __init__(self, smtp_server: str, port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password

    def send(self, message) -> None:
        email = PyEmailMessage()
        email["From"] = message.sender
        email["To"] = message.receiver
        email["Subject"] = message.subject
        email.set_content(message.body)

        for attachment in message.attachments:
            email.add_attachment(
                attachment.get_bytes(),
                maintype="application",
                subtype="pdf",
                filename=attachment.get_filename(),
            )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
            Logger.info("Connecting to SMTP server...")
            server.login(self.username, self.password)
            server.send_message(email)
            Logger.success(f"Email sent to {message.receiver}")
