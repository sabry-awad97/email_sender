"""Send command implementation."""

from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from config.schema import AppConfig
from core.attachment import FileAttachment
from core.email_service import EmailService
from infrastructure.logger import Logger
from infrastructure.smtp_client import SMTPClient, SMTPClientError
from models.email_message import EmailMessageModel

console = Console()


@click.group()
def send_command():
    """Send emails with various options."""
    pass


@send_command.command("single")
@click.option("--to", "-t", required=True, multiple=True, help="Recipient email address(es)")
@click.option("--subject", "-s", help="Email subject")
@click.option("--body", "-b", help="Email body text")
@click.option(
    "--body-file",
    type=click.Path(exists=True, path_type=Path),
    help="Read email body from file",
)
@click.option(
    "--attach",
    "-a",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="File to attach (can be used multiple times)",
)
@click.option("--template", help="Use email template by name")
@click.option("--from", "sender", help="Sender email address (overrides config)")
@click.option("--dry-run", is_flag=True, help="Show what would be sent without actually sending")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode for composing email")
@click.pass_context
def single(
    ctx: click.Context,
    to: tuple[str] | None,
    subject: str | None,
    body: str | None,
    body_file: Path | None,
    attach: tuple[Path] | None,
    template: str | None,
    sender: str | None,
    dry_run: bool,
    interactive: bool,
):
    """
    Send a single email to one or more recipients.

    Examples:

        # Simple email
        email-sender send single --to user@example.com --subject "Hello" --body "World"

        # With attachment
        email-sender send single --to user@example.com --subject "Report" --attach report.pdf

        # Using template
        email-sender send single --to user@example.com --template welcome

        # Interactive mode
        email-sender send single --interactive
    """
    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print(
            "[red]Error:[/red] No configuration loaded. Run 'email-sender config init' first."
        )
        raise click.Abort()

    try:
        # Interactive mode
        if interactive:
            to, subject, body, attach, sender = _interactive_compose(
                config, to, subject, body, attach, sender
            )

        # Validate and prepare email data
        recipients = list(to) if to else []
        if not recipients:
            console.print("[red]Error:[/red] At least one recipient is required.")
            raise click.Abort()

        # Use template if specified
        if template:
            if template not in config.templates:
                console.print(f"[red]Error:[/red] Template '{template}' not found.")
                raise click.Abort()

            template_config = config.templates[template]
            subject = subject or template_config.subject
            body = body or template_config.body

            # Add template attachments if no explicit attachments provided
            if not attach and template_config.attachments:
                attach = tuple(Path(p) for p in template_config.attachments)

        # Read body from file if specified
        if body_file:
            try:
                body = body_file.read_text(encoding="utf-8")
            except OSError as e:
                console.print(f"[red]Error:[/red] Failed to read body file: {e}")
                raise click.Abort() from e

        # Ensure required fields
        if not subject:
            subject = Prompt.ask("Email subject") if interactive else "Email from CLI"
        if not body:
            body = (
                Prompt.ask("Email body")
                if interactive
                else "This email was sent using the email-sender CLI."
            )

        # Determine sender
        email_sender = sender or config.default_sender or config.smtp.username
        if not email_sender:
            console.print(
                "[red]Error:[/red] No sender email specified. Set default_sender in config or use --from."
            )
            raise click.Abort()

        # Process attachments
        attachments = []
        total_size = 0

        for attachment_path in attach:
            try:
                attachment = FileAttachment(str(attachment_path))
                size = attachment.get_size()
                total_size += size

                if total_size > config.attachment_max_size:
                    console.print(
                        f"[red]Error:[/red] Total attachment size ({total_size:,} bytes) "
                        f"exceeds limit ({config.attachment_max_size:,} bytes)"
                    )
                    raise click.Abort()

                attachments.append(attachment)
                Logger.info(f"Added attachment: {attachment.get_filename()} ({size:,} bytes)")

            except (FileNotFoundError, ValueError) as e:
                console.print(f"[red]Error:[/red] Attachment error: {e}")
                raise click.Abort() from e

        # Send to each recipient
        for recipient in recipients:
            message = EmailMessageModel(
                sender=email_sender,
                receiver=recipient,
                subject=subject,
                body=body,
                attachments=attachments,
            )

            if dry_run:
                _show_email_preview(message)
                continue

            # Send the email
            try:
                smtp_client = SMTPClient(
                    smtp_server=config.smtp.server,
                    port=config.smtp.port,
                    username=config.smtp.username,
                    password=config.smtp.password,
                    use_tls=config.smtp.use_tls,
                )

                service = EmailService(smtp_client)
                service.send_email(message)

                console.print(f"[green]✓[/green] Email sent successfully to {recipient}")

            except SMTPClientError as e:
                console.print(f"[red]✗[/red] Failed to send email to {recipient}: {e}")
                Logger.error(f"Failed to send email to {recipient}: {e}")

    except Exception as e:
        Logger.exception("Unexpected error in send command")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


def _interactive_compose(
    config: AppConfig,
    to: tuple[str] | None,
    subject: str | None,
    body: str | None,
    attach: tuple[Path] | None,
    sender: str | None,
) -> tuple[str, str, str, tuple[Path], str]:
    """Interactive email composition."""
    console.print("[bold]Interactive Email Composition[/bold]")

    # Recipients
    if not to:
        recipients = []
        while True:
            recipient = Prompt.ask("Recipient email (press Enter when done)")
            if not recipient:
                break
            recipients.append(recipient)
        to = tuple(recipients)

    # Subject
    if not subject:
        subject = Prompt.ask("Subject", default="Email from CLI")

    # Body
    if not body:
        console.print("Enter email body (press Ctrl+D when finished):")
        body_lines = []
        try:
            while True:
                line = input()
                body_lines.append(line)
        except EOFError:
            pass
        body = "\n".join(body_lines)

    # Attachments
    if not attach:
        attachments = []
        while True:
            attachment_path = Prompt.ask("Attachment path (press Enter when done)", default="")
            if not attachment_path:
                break
            path = Path(attachment_path)
            if path.exists():
                attachments.append(path)
            else:
                console.print(f"[yellow]Warning:[/yellow] File not found: {attachment_path}")
        attach = tuple(attachments)

    # Sender
    if not sender:
        default_sender = config.default_sender or config.smtp.username
        sender = Prompt.ask("Sender email", default=default_sender)

    return to, subject, body, attach, sender


def _show_email_preview(message: EmailMessageModel):
    """Show a preview of the email that would be sent."""
    console.print("\n[bold]Email Preview (Dry Run)[/bold]")
    console.print(f"[cyan]From:[/cyan] {message.sender}")
    console.print(f"[cyan]To:[/cyan] {message.receiver}")
    console.print(f"[cyan]Subject:[/cyan] {message.subject}")
    console.print("[cyan]Body:[/cyan]")
    console.print(message.body)

    if message.attachments:
        console.print("[cyan]Attachments:[/cyan]")
        for attachment in message.attachments:
            console.print(f"  - {attachment.get_filename()} ({attachment.get_size():,} bytes)")

    console.print()


@send_command.command("bulk")
@click.option(
    "--recipients-file",
    "-r",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="File containing recipient email addresses (one per line)",
)
@click.option("--subject", "-s", help="Email subject")
@click.option("--body", "-b", help="Email body text")
@click.option(
    "--body-file",
    type=click.Path(exists=True, path_type=Path),
    help="Read email body from file",
)
@click.option(
    "--attach",
    "-a",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="File to attach (can be used multiple times)",
)
@click.option("--template", help="Use email template by name")
@click.option("--from", "sender", help="Sender email address (overrides config)")
@click.option("--dry-run", is_flag=True, help="Show what would be sent without actually sending")
@click.option("--delay", type=float, default=1.0, help="Delay between emails in seconds")
@click.pass_context
def bulk(
    ctx: click.Context,
    recipients_file: Path,
    subject: str | None,
    body: str | None,
    body_file: Path | None,
    attach: tuple[Path],
    template: str | None,
    sender: str | None,
    dry_run: bool,
    delay: float,
):
    """
    Send bulk emails to multiple recipients from a file.

    The recipients file should contain one email address per line.
    Comments (lines starting with #) and empty lines are ignored.

    Examples:

        # Send to all recipients in file
        email-sender send bulk --recipients-file emails.txt --subject "Newsletter"

        # With template and delay
        email-sender send bulk -r emails.txt --template newsletter --delay 2.0
    """
    import time

    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print(
            "[red]Error:[/red] No configuration loaded. Run 'email-sender config init' first."
        )
        raise click.Abort()

    # Read recipients from file
    try:
        recipients = []
        with open(recipients_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    recipients.append(line)

        if not recipients:
            console.print("[red]Error:[/red] No valid recipients found in file.")
            raise click.Abort()

        console.print(f"Found {len(recipients)} recipients")

    except OSError as e:
        console.print(f"[red]Error:[/red] Failed to read recipients file: {e}")
        raise click.Abort() from e

    # Confirm bulk send
    if not dry_run and not Confirm.ask(f"Send email to {len(recipients)} recipients?"):
        console.print("Bulk send cancelled.")
        return

    # Send emails using single command logic
    success_count = 0
    error_count = 0

    with console.status("[bold green]Sending emails...") as status:
        for i, recipient in enumerate(recipients, 1):
            status.update(f"[bold green]Sending email {i}/{len(recipients)} to {recipient}...")

            try:
                # Use the single command logic
                ctx.invoke(
                    single,
                    to=(recipient,),
                    subject=subject,
                    body=body,
                    body_file=body_file,
                    attach=attach,
                    template=template,
                    sender=sender,
                    dry_run=dry_run,
                )
                success_count += 1

            except click.Abort:
                error_count += 1
                continue

            # Add delay between emails (except for last one)
            if i < len(recipients) and not dry_run:
                time.sleep(delay)

    # Summary
    console.print("\n[bold]Bulk Send Summary[/bold]")
    console.print(f"[green]Successful:[/green] {success_count}")
    console.print(f"[red]Failed:[/red] {error_count}")
    console.print(f"[blue]Total:[/blue] {len(recipients)}")


# Make send_command the default export
__all__ = ["send_command"]
