import smtplib
import ssl
from email.message import EmailMessage as PyEmailMessage

from core.interfaces import IEmailClient
from infrastructure.logger import Logger


class SMTPClientError(Exception):
    """SMTP client specific errors."""

    pass


class SMTPClient(IEmailClient):
    """Concrete SMTP implementation of IEmailClient."""

    def __init__(
        self,
        smtp_server: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(self, message) -> None:
        """Send an email message via SMTP."""
        try:
            email = self._build_email_message(message)
            self._send_via_smtp(email, message.receiver)
            Logger.success(f"Email sent successfully to {message.receiver}")
        except Exception as e:
            Logger.error(f"Failed to send email to {message.receiver}: {str(e)}")
            raise SMTPClientError(f"Failed to send email: {str(e)}") from e

    def _build_email_message(self, message) -> PyEmailMessage:
        """Build the email message with attachments."""
        email = PyEmailMessage()
        email["From"] = message.sender
        email["To"] = message.receiver
        email["Subject"] = message.subject
        email.set_content(message.body)

        # Add attachments with proper MIME types
        for attachment in message.attachments:
            try:
                main_type, sub_type = attachment.get_mime_type()
                email.add_attachment(
                    attachment.get_bytes(),
                    maintype=main_type,
                    subtype=sub_type,
                    filename=attachment.get_filename(),
                )
                Logger.info(
                    f"Added attachment: {attachment.get_filename()} ({attachment.get_size()} bytes)"
                )
            except Exception as e:
                Logger.error(f"Failed to add attachment {attachment.get_filename()}: {str(e)}")
                raise

        return email

    def _send_via_smtp(self, email: PyEmailMessage, recipients: str) -> None:
        """Send email via SMTP connection."""
        Logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.port}")

        context = ssl.create_default_context()

        try:
            if self.use_tls:
                with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                    self._authenticate_and_send(server, email, recipients)
            else:
                with smtplib.SMTP(self.smtp_server, self.port) as server:
                    server.starttls(context=context)
                    self._authenticate_and_send(server, email, recipients)
        except smtplib.SMTPException as e:
            raise SMTPClientError(f"SMTP error: {str(e)}") from e
        except Exception as e:
            raise SMTPClientError(f"Connection error: {str(e)}") from e

    def _authenticate_and_send(
        self, server: smtplib.SMTP, email: PyEmailMessage, recipients: str
    ) -> None:
        """Authenticate with SMTP server and send the message."""
        try:
            Logger.info("Authenticating with SMTP server...")
            server.login(self.username, self.password)
            Logger.info("Authentication successful")

            server.send_message(email)
            Logger.info("Message sent successfully")
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPClientError(f"Authentication failed: {str(e)}") from e
        except smtplib.SMTPException as e:
            raise SMTPClientError(f"Failed to send message: {str(e)}") from e
