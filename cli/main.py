"""Main CLI entry point for email-sender application."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cli.commands.config import config_command
from cli.commands.send import send_command
from cli.commands.template import template_command
from config.manager import ConfigManager, ConfigurationError
from infrastructure.logger import Logger

console = Console()


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.version_option(version="0.1.0", prog_name="email-sender")
@click.pass_context
def cli(ctx: click.Context, config: Path | None, verbose: bool, quiet: bool):
    """
    Email Sender CLI - A robust tool for sending emails with attachments.

    This CLI provides commands to send emails, manage configurations, and work with templates.
    Configuration can be provided via YAML files or environment variables.

    Examples:

        # Send a simple email
        email-sender send --to user@example.com --subject "Hello" --body "World"

        # Send with attachment
        email-sender send --to user@example.com --subject "Report" --attach report.pdf

        # Create configuration
        email-sender config init

        # List templates
        email-sender template list
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Setup logging based on verbosity
    if quiet:
        log_level = "ERROR"
    elif verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    # Initialize configuration manager
    config_manager = ConfigManager(config_path=config)
    ctx.obj["config_manager"] = config_manager

    try:
        # Load configuration
        app_config = config_manager.load_config()
        ctx.obj["config"] = app_config

        # Setup logging with config
        Logger.setup(
            level=log_level,
            log_file=app_config.logging.file,
            console=app_config.logging.console and not quiet,
            format_string=app_config.logging.format,
        )

    except ConfigurationError as e:
        # If config loading fails, setup basic logging and continue
        Logger.setup(level=log_level, console=not quiet)
        ctx.obj["config"] = None

        if not quiet:
            console.print(f"[yellow]Warning:[/yellow] {e}")
            console.print(
                "[yellow]Some commands may not work without proper configuration.[/yellow]"
            )


@cli.command()
@click.pass_context
def version(ctx: click.Context):
    """Show version information."""
    console.print("[bold]Email Sender CLI[/bold] version [green]0.1.0[/green]")

    config = ctx.obj.get("config")
    if config:
        console.print(
            f"Configuration loaded from: [blue]{ctx.obj['config_manager'].config_file_path}[/blue]"
        )
    else:
        console.print("[yellow]No configuration loaded[/yellow]")


@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """Show application status and configuration."""
    config = ctx.obj.get("config")
    config_manager = ctx.obj["config_manager"]

    table = Table(title="Email Sender Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Configuration status
    if config:
        table.add_row("Configuration", "✓ Loaded", str(config_manager.config_file_path))
        table.add_row("SMTP Server", "✓ Configured", f"{config.smtp.server}:{config.smtp.port}")
        table.add_row(
            "Default Sender",
            "✓ Set" if config.default_sender else "⚠ Not set",
            str(config.default_sender) if config.default_sender else "None",
        )
        table.add_row(
            "Templates",
            f"✓ {len(config.templates)}",
            f"{len(config.templates)} template(s)",
        )
    else:
        table.add_row("Configuration", "✗ Not loaded", "Run 'email-sender config init' to create")
        table.add_row("SMTP Server", "✗ Not configured", "Configuration required")
        table.add_row("Default Sender", "✗ Not set", "Configuration required")
        table.add_row("Templates", "✗ Not available", "Configuration required")

    console.print(table)


# Add command groups
cli.add_command(send_command, name="send")
cli.add_command(config_command, name="config")
cli.add_command(template_command, name="template")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        Logger.exception("Unexpected error occurred")
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
