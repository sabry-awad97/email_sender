from config.settings import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, APP_PASSWORD
from models.email_message import EmailMessageModel
from core.email_service import EmailService
from core.attachment import PDFAttachment
from infrastructure.smtp_client import SMTPClient

def main():
    # Build email message
    message = EmailMessageModel(
        sender=SENDER_EMAIL,
        receiver="tdamon@axiosint.com",
        subject="Professional PDF Delivery",
        body="Dear Sir,\n\nPlease find the attached PDF document.\n\nBest regards,\nDr. Sabry",
        attachments=[PDFAttachment("document.pdf")]
    )

    # Inject SMTP client into email service (DIP)
    smtp_client = SMTPClient(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, APP_PASSWORD)
    service = EmailService(smtp_client)

    # Send email
    service.send_email(message)

if __name__ == "__main__":
    main()
