"""Configuration management commands."""

from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from config.manager import ConfigManager
from config.schema import AppConfig, ConfigDefaults
from infrastructure.logger import Logger

console = Console()


@click.group()
def config_command():
    """Manage email sender configuration."""
    pass


@config_command.command("init")
@click.option(
    "--path",
    "-p",
    type=click.Path(path_type=Path),
    help="Configuration file path (default: ~/.email-sender/config.yaml)",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
@click.option("--interactive", "-i", is_flag=True, help="Interactive configuration setup")
@click.pass_context
def init(ctx: click.Context, path: Path | None, force: bool, interactive: bool):
    """
    Initialize a new configuration file.

    Creates a configuration file with default values or prompts for interactive setup.

    Examples:

        # Create default config
        email-sender config init

        # Interactive setup
        email-sender config init --interactive

        # Custom path
        email-sender config init --path ./my-config.yaml
    """
    config_manager: ConfigManager = ctx.obj["config_manager"]

    # Determine config path
    if path:
        config_path = path
    else:
        config_path = config_manager.DEFAULT_CONFIG_PATHS[0]

    # Check if config already exists
    if config_path.exists() and not force:
        if not Confirm.ask(f"Configuration file already exists at {config_path}. Overwrite?"):
            console.print("Configuration initialization cancelled.")
            return

    try:
        if interactive:
            config_data = _interactive_config_setup()
        else:
            config_data = _create_default_config()

        # Validate configuration
        app_config = AppConfig(**config_data)

        # Save configuration
        saved_path = config_manager.save_config(app_config, config_path)

        console.print(f"[green]✓[/green] Configuration created at: [blue]{saved_path}[/blue]")
        console.print("\n[yellow]Important:[/yellow] Remember to update your SMTP credentials!")
        console.print("You can edit the file directly or use 'email-sender config set' commands.")

    except Exception as e:
        Logger.exception("Failed to initialize configuration")
        console.print(f"[red]Error:[/red] Failed to create configuration: {e}")
        raise click.Abort() from e


@config_command.command("show")
@click.option("--section", "-s", help="Show specific configuration section")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def show(ctx: click.Context, section: str | None, output_format: str):
    """
    Display current configuration.

    Examples:

        # Show all configuration
        email-sender config show

        # Show specific section
        email-sender config show --section smtp

        # Show as YAML
        email-sender config show --format yaml
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        console.print("Run 'email-sender config init' to create a configuration file.")
        raise click.Abort()

    config_dict = config.model_dump()

    # Filter by section if specified
    if section:
        if section not in config_dict:
            console.print(f"[red]Error:[/red] Configuration section '{section}' not found.")
            console.print(f"Available sections: {', '.join(config_dict.keys())}")
            raise click.Abort()
        config_dict = {section: config_dict[section]}

    if output_format == "yaml":
        yaml_output = yaml.dump(config_dict, default_flow_style=False, indent=2)
        syntax = Syntax(yaml_output, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        _show_config_table(config_dict, config_manager.config_file_path)


@config_command.command("set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--type",
    "value_type",
    type=click.Choice(["string", "int", "bool"]),
    default="string",
    help="Value type",
)
@click.pass_context
def set_value(ctx: click.Context, key: str, value: str, value_type: str):
    """
    Set a configuration value.

    Use dot notation to specify nested keys (e.g., smtp.server).

    Examples:

        # Set SMTP server
        email-sender config set smtp.server smtp.gmail.com

        # Set port (as integer)
        email-sender config set smtp.port 587 --type int

        # Set boolean value
        email-sender config set smtp.use_tls true --type bool
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    try:
        # Convert value to appropriate type
        if value_type == "int":
            converted_value = int(value)
        elif value_type == "bool":
            converted_value = value.lower() in ("true", "1", "yes", "on")
        else:
            converted_value = value

        # Update configuration
        config_dict = config.model_dump()
        _set_nested_value(config_dict, key, converted_value)

        # Validate updated configuration
        updated_config = AppConfig(**config_dict)

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(updated_config, config_path)

        console.print(f"[green]✓[/green] Configuration updated: {key} = {converted_value}")

        # Update context
        ctx.obj["config"] = updated_config

    except (ValueError, TypeError) as e:
        console.print(f"[red]Error:[/red] Invalid value: {e}")
        raise click.Abort() from e
    except Exception as e:
        Logger.exception("Failed to set configuration value")
        console.print(f"[red]Error:[/red] Failed to update configuration: {e}")
        raise click.Abort() from e


@config_command.command("validate")
@click.pass_context
def validate(ctx: click.Context):
    """
    Validate the current configuration.

    Checks configuration syntax and tests SMTP connection.
    """
    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    console.print("[bold]Validating Configuration[/bold]")

    # Basic validation (already done during loading)
    console.print("[green]✓[/green] Configuration syntax is valid")

    # Test SMTP connection
    try:
        console.print("Testing SMTP connection...")

        # Try to connect and authenticate
        import smtplib
        import ssl

        context = ssl.create_default_context()

        if config.smtp.use_tls:
            with smtplib.SMTP_SSL(config.smtp.server, config.smtp.port, context=context) as server:
                server.login(config.smtp.username, config.smtp.password)
        else:
            with smtplib.SMTP(config.smtp.server, config.smtp.port) as server:
                server.starttls(context=context)
                server.login(config.smtp.username, config.smtp.password)

        console.print("[green]✓[/green] SMTP connection successful")

    except Exception as e:
        console.print(f"[red]✗[/red] SMTP connection failed: {e}")
        console.print("[yellow]Check your SMTP credentials and server settings.[/yellow]")


@config_command.command("path")
@click.pass_context
def path(ctx: click.Context):
    """Show the path to the current configuration file."""
    config_manager: ConfigManager = ctx.obj["config_manager"]

    config_path = config_manager.config_file_path
    if config_path:
        console.print(f"Configuration file: [blue]{config_path}[/blue]")
    else:
        console.print("[yellow]No configuration file found.[/yellow]")
        console.print("Default search paths:")
        for path in config_manager.DEFAULT_CONFIG_PATHS:
            console.print(f"  - {path}")


def _interactive_config_setup() -> dict:
    """Interactive configuration setup."""
    console.print("[bold]Interactive Configuration Setup[/bold]")

    config_data = {}

    # SMTP Configuration
    console.print("\n[cyan]SMTP Configuration[/cyan]")

    # Choose provider or custom
    provider = Prompt.ask(
        "Choose SMTP provider",
        choices=["gmail", "outlook", "yahoo", "custom"],
        default="gmail",
    )

    if provider != "custom":
        smtp_config = ConfigDefaults.SMTP_SERVERS[provider].copy()
        console.print(f"Using {provider} settings: {smtp_config['server']}:{smtp_config['port']}")
    else:
        smtp_config = {
            "server": Prompt.ask("SMTP server"),
            "port": int(Prompt.ask("SMTP port", default="587")),
            "use_tls": Confirm.ask("Use TLS/SSL?", default=True),
        }

    smtp_config["username"] = Prompt.ask("SMTP username/email")
    smtp_config["password"] = Prompt.ask("SMTP password", password=True)

    config_data["smtp"] = smtp_config

    # Default sender
    default_sender = Prompt.ask("Default sender email", default=smtp_config["username"])
    if default_sender:
        config_data["default_sender"] = default_sender

    # Logging
    console.print("\n[cyan]Logging Configuration[/cyan]")
    log_level = Prompt.ask(
        "Log level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    log_to_file = Confirm.ask("Log to file?", default=False)

    logging_config = {"level": log_level, "console": True}

    if log_to_file:
        log_file = Prompt.ask("Log file path", default="email-sender.log")
        logging_config["file"] = log_file

    config_data["logging"] = logging_config

    return config_data


def _create_default_config() -> dict:
    """Create default configuration with placeholder values."""
    return {
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 465,
            "use_tls": True,
            "username": "your-email@gmail.com",
            "password": "your-app-password",
        },
        "default_sender": "your-email@gmail.com",
        "logging": {"level": "INFO", "console": True},
        "templates": {
            "default": {
                "name": "default",
                "subject": "Email from CLI",
                "body": "This email was sent using the email-sender CLI tool.",
                "attachments": [],
            }
        },
    }


def _show_config_table(config_dict: dict, config_path: Path | None):
    """Display configuration as a formatted table."""
    table = Table(title=f"Configuration ({config_path or 'Not saved'})")
    table.add_column("Section", style="cyan")
    table.add_column("Key", style="yellow")
    table.add_column("Value", style="green")

    for section, section_data in config_dict.items():
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                # Hide password values
                if "password" in key.lower():
                    value = "***"
                table.add_row(section, key, str(value))
        else:
            table.add_row(section, "", str(section_data))

    console.print(table)


def _set_nested_value(config_dict: dict, key: str, value):
    """Set a nested dictionary value using dot notation."""
    keys = key.split(".")
    current = config_dict

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value


# Make config_command the default export
__all__ = ["config_command"]
