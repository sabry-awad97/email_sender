"""Template management commands."""

from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from config.manager import ConfigManager
from config.schema import AppConfig, EmailTemplate
from infrastructure.logger import Logger

console = Console()


@click.group()
def template_command():
    """Manage email templates."""
    pass


@template_command.command("list")
@click.pass_context
def list_templates(ctx: click.Context):
    """
    List all available email templates.

    Shows template names, subjects, and attachment counts.
    """
    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    if not config.templates:
        console.print("[yellow]No templates found.[/yellow]")
        console.print("Create a template with: email-sender template create")
        return

    table = Table(title="Email Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Subject", style="yellow")
    table.add_column("Body Preview", style="white")
    table.add_column("Attachments", style="green")

    for name, template in config.templates.items():
        body_preview = template.body[:50] + "..." if len(template.body) > 50 else template.body
        body_preview = body_preview.replace("\n", " ")

        attachment_count = len(template.attachments)
        attachment_text = f"{attachment_count} file(s)" if attachment_count > 0 else "None"

        table.add_row(name, template.subject, body_preview, attachment_text)

    console.print(table)


@template_command.command("show")
@click.argument("name")
@click.pass_context
def show_template(ctx: click.Context, name: str):
    """
    Show detailed information about a specific template.

    NAME: Template name to display
    """
    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    if name not in config.templates:
        console.print(f"[red]Error:[/red] Template '{name}' not found.")
        _suggest_templates(config.templates.keys())
        raise click.Abort()

    template = config.templates[name]

    console.print(f"[bold]Template: {name}[/bold]")
    console.print(f"[cyan]Subject:[/cyan] {template.subject}")
    console.print("[cyan]Body:[/cyan]")
    console.print(template.body)

    if template.attachments:
        console.print("[cyan]Attachments:[/cyan]")
        for attachment in template.attachments:
            path = Path(attachment)
            if path.exists():
                console.print(f"  ✓ {attachment}")
            else:
                console.print(f"  ✗ {attachment} [red](not found)[/red]")
    else:
        console.print("[cyan]Attachments:[/cyan] None")


@template_command.command("create")
@click.argument("name")
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
    type=click.Path(path_type=Path),
    help="Default attachment paths",
)
@click.option("--interactive", "-i", is_flag=True, help="Interactive template creation")
@click.pass_context
def create_template(
    ctx: click.Context,
    name: str,
    subject: str | None,
    body: str | None,
    body_file: Path | None,
    attach: tuple,
    interactive: bool,
):
    """
    Create a new email template.

    NAME: Template name (must be unique)

    Examples:

        # Simple template
        email-sender template create welcome --subject "Welcome!" --body "Welcome to our service"

        # Interactive creation
        email-sender template create newsletter --interactive

        # With body from file
        email-sender template create report --body-file template.txt
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    # Check if template already exists
    if name in config.templates:
        if not Confirm.ask(f"Template '{name}' already exists. Overwrite?"):
            console.print("Template creation cancelled.")
            return

    try:
        # Interactive mode
        if interactive:
            subject, body, attach = _interactive_template_creation(subject, body, attach)

        # Read body from file if specified
        if body_file:
            try:
                body = body_file.read_text(encoding="utf-8")
            except OSError as e:
                console.print(f"[red]Error:[/red] Failed to read body file: {e}")
                raise click.Abort() from e

        # Ensure required fields
        if not subject:
            subject = Prompt.ask("Template subject")
        if not body:
            body = Prompt.ask("Template body")

        # Validate attachment paths
        attachment_paths = []
        for attachment_path in attach:
            path = Path(attachment_path)
            if not path.exists():
                if not Confirm.ask(
                    f"Attachment file '{attachment_path}' does not exist. Include anyway?"
                ):
                    continue
            attachment_paths.append(str(attachment_path))

        # Create template
        template = EmailTemplate(
            name=name, subject=subject, body=body, attachments=attachment_paths
        )

        # Update configuration
        config.templates[name] = template

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(config, config_path)

        console.print(f"[green]✓[/green] Template '{name}' created successfully")

        # Update context
        ctx.obj["config"] = config

    except Exception as e:
        Logger.exception("Failed to create template")
        console.print(f"[red]Error:[/red] Failed to create template: {e}")
        raise click.Abort() from e


@template_command.command("edit")
@click.argument("name")
@click.option("--subject", "-s", help="New email subject")
@click.option("--body", "-b", help="New email body text")
@click.option(
    "--body-file",
    type=click.Path(exists=True, path_type=Path),
    help="Read new email body from file",
)
@click.option(
    "--add-attach",
    multiple=True,
    type=click.Path(path_type=Path),
    help="Add attachment paths",
)
@click.option("--remove-attach", multiple=True, help="Remove attachment paths")
@click.option("--interactive", "-i", is_flag=True, help="Interactive template editing")
@click.pass_context
def edit_template(
    ctx: click.Context,
    name: str,
    subject: str | None,
    body: str | None,
    body_file: Path | None,
    add_attach: tuple,
    remove_attach: tuple,
    interactive: bool,
):
    """
    Edit an existing email template.

    NAME: Template name to edit

    Examples:

        # Update subject
        email-sender template edit welcome --subject "New Welcome Message"

        # Interactive editing
        email-sender template edit newsletter --interactive

        # Add attachment
        email-sender template edit report --add-attach report.pdf
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    if name not in config.templates:
        console.print(f"[red]Error:[/red] Template '{name}' not found.")
        _suggest_templates(config.templates.keys())
        raise click.Abort()

    template = config.templates[name]

    try:
        # Interactive mode
        if interactive:
            subject, body, add_attach, remove_attach = _interactive_template_edit(
                template, subject, body, add_attach, remove_attach
            )

        # Update fields
        if subject is not None:
            template.subject = subject

        if body_file:
            try:
                template.body = body_file.read_text(encoding="utf-8")
            except OSError as e:
                console.print(f"[red]Error:[/red] Failed to read body file: {e}")
                raise click.Abort() from e
        elif body is not None:
            template.body = body

        # Handle attachments
        current_attachments = set(template.attachments)

        # Add new attachments
        for attachment_path in add_attach:
            path = Path(attachment_path)
            if not path.exists():
                if not Confirm.ask(
                    f"Attachment file '{attachment_path}' does not exist. Add anyway?"
                ):
                    continue
            current_attachments.add(str(attachment_path))

        # Remove attachments
        for attachment_path in remove_attach:
            current_attachments.discard(attachment_path)

        template.attachments = list(current_attachments)

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(config, config_path)

        console.print(f"[green]✓[/green] Template '{name}' updated successfully")

        # Update context
        ctx.obj["config"] = config

    except Exception as e:
        Logger.exception("Failed to edit template")
        console.print(f"[red]Error:[/red] Failed to edit template: {e}")
        raise click.Abort() from e


@template_command.command("delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Delete without confirmation")
@click.pass_context
def delete_template(ctx: click.Context, name: str, force: bool):
    """
    Delete an email template.

    NAME: Template name to delete
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    if name not in config.templates:
        console.print(f"[red]Error:[/red] Template '{name}' not found.")
        _suggest_templates(config.templates.keys())
        raise click.Abort()

    # Confirm deletion
    if not force and not Confirm.ask(f"Delete template '{name}'?"):
        console.print("Template deletion cancelled.")
        return

    try:
        # Remove template
        del config.templates[name]

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(config, config_path)

        console.print(f"[green]✓[/green] Template '{name}' deleted successfully")

        # Update context
        ctx.obj["config"] = config

    except Exception as e:
        Logger.exception("Failed to delete template")
        console.print(f"[red]Error:[/red] Failed to delete template: {e}")
        raise click.Abort() from e


@template_command.command("copy")
@click.argument("source")
@click.argument("destination")
@click.pass_context
def copy_template(ctx: click.Context, source: str, destination: str):
    """
    Copy an existing template to a new name.

    SOURCE: Name of template to copy
    DESTINATION: Name for the new template
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        raise click.Abort()

    if source not in config.templates:
        console.print(f"[red]Error:[/red] Source template '{source}' not found.")
        _suggest_templates(config.templates.keys())
        raise click.Abort()

    if destination in config.templates:
        if not Confirm.ask(f"Template '{destination}' already exists. Overwrite?"):
            console.print("Template copy cancelled.")
            return

    try:
        # Copy template
        source_template = config.templates[source]
        new_template = EmailTemplate(
            name=destination,
            subject=source_template.subject,
            body=source_template.body,
            attachments=source_template.attachments.copy(),
        )

        config.templates[destination] = new_template

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(config, config_path)

        console.print(f"[green]✓[/green] Template '{source}' copied to '{destination}'")

        # Update context
        ctx.obj["config"] = config

    except Exception as e:
        Logger.exception("Failed to copy template")
        console.print(f"[red]Error:[/red] Failed to copy template: {e}")
        raise click.Abort() from e


def _interactive_template_creation(subject: str | None, body: str | None, attach: tuple) -> tuple:
    """Interactive template creation."""
    console.print("[bold]Interactive Template Creation[/bold]")

    # Subject
    if not subject:
        subject = Prompt.ask("Template subject")

    # Body
    if not body:
        console.print("Enter template body (press Ctrl+D when finished):")
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
            attachment_path = Prompt.ask(
                "Default attachment path (press Enter when done)", default=""
            )
            if not attachment_path:
                break
            attachments.append(Path(attachment_path))
        attach = tuple(attachments)

    return subject, body, attach


def _interactive_template_edit(
    template: EmailTemplate,
    subject: str | None,
    body: str | None,
    add_attach: tuple,
    remove_attach: tuple,
) -> tuple:
    """Interactive template editing."""
    console.print(f"[bold]Editing Template: {template.name}[/bold]")

    # Subject
    if subject is None:
        new_subject = Prompt.ask("Subject", default=template.subject)
        subject = new_subject if new_subject != template.subject else None

    # Body
    if body is None:
        console.print(f"Current body:\n{template.body}")
        if Confirm.ask("Edit body?"):
            console.print("Enter new body (press Ctrl+D when finished):")
            body_lines = []
            try:
                while True:
                    line = input()
                    body_lines.append(line)
            except EOFError:
                pass
            body = "\n".join(body_lines)

    # Attachments
    if not add_attach and not remove_attach:
        console.print(
            f"Current attachments: {', '.join(template.attachments) if template.attachments else 'None'}"
        )

        # Add attachments
        new_attachments = []
        while True:
            attachment_path = Prompt.ask("Add attachment path (press Enter when done)", default="")
            if not attachment_path:
                break
            new_attachments.append(Path(attachment_path))
        add_attach = tuple(new_attachments)

        # Remove attachments
        if template.attachments:
            remove_list = []
            for attachment in template.attachments:
                if Confirm.ask(f"Remove attachment '{attachment}'?"):
                    remove_list.append(attachment)
            remove_attach = tuple(remove_list)

    return subject, body, add_attach, remove_attach


@template_command.command("import")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--overwrite", is_flag=True, help="Overwrite existing templates")
@click.pass_context
def import_templates(ctx: click.Context, file_path: Path, overwrite: bool):
    """Import templates from a JSON or YAML file.

    FILE_PATH: Path to the template file to import

    Examples:
        # Import templates from JSON
        email-sender template import templates.json

        # Import with overwrite
        email-sender template import templates.yaml --overwrite
    """
    config: AppConfig | None = ctx.obj.get("config")
    config_manager: ConfigManager = ctx.obj["config_manager"]

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        console.print("Run 'email-sender config init' to create a configuration file.")
        raise click.Abort()

    try:
        # Read template file
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            import yaml

            with open(file_path, encoding="utf-8") as f:
                template_data = yaml.safe_load(f)
        elif file_path.suffix.lower() == ".json":
            import json

            with open(file_path, encoding="utf-8") as f:
                template_data = json.load(f)
        else:
            console.print("[red]Error:[/red] Unsupported file format. Use JSON or YAML.")
            raise click.Abort()

        # Import templates
        imported_count = 0
        skipped_count = 0

        for name, template_info in template_data.items():
            if name in config.templates and not overwrite:
                console.print(f"[yellow]Skipped:[/yellow] Template '{name}' already exists")
                skipped_count += 1
                continue

            # Create template
            template = EmailTemplate(
                name=name,
                subject=template_info.get("subject", ""),
                body=template_info.get("body", ""),
                attachments=template_info.get("attachments", []),
            )

            config.templates[name] = template
            imported_count += 1
            console.print(f"[green]✓[/green] Imported template: {name}")

        # Save configuration
        config_path = config_manager.config_file_path or config_manager.DEFAULT_CONFIG_PATHS[0]
        config_manager.save_config(config, config_path)

        console.print(
            f"\n[green]✓[/green] Import complete: {imported_count} imported, {skipped_count} skipped"
        )

    except Exception as e:
        Logger.exception("Failed to import templates")
        console.print(f"[red]Error:[/red] Failed to import templates: {e}")
        raise click.Abort() from e


@template_command.command("export")
@click.argument("file_path", type=click.Path(path_type=Path))
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    help="Export format",
)
@click.option("--templates", multiple=True, help="Specific templates to export (default: all)")
@click.pass_context
def export_templates(ctx: click.Context, file_path: Path, export_format: str, templates: tuple):
    """Export templates to a JSON or YAML file.

    FILE_PATH: Path where to save the exported templates

    Examples:
        # Export all templates to YAML
        email-sender template export templates.yaml

        # Export specific templates to JSON
        email-sender template export templates.json --format json --templates welcome --templates newsletter
    """
    config: AppConfig | None = ctx.obj.get("config")

    if not config:
        console.print("[red]Error:[/red] No configuration loaded.")
        console.print("Run 'email-sender config init' to create a configuration file.")
        raise click.Abort()

    if not config.templates:
        console.print("[yellow]Warning:[/yellow] No templates to export.")
        return

    try:
        # Select templates to export
        if templates:
            export_templates_dict = {}
            for template_name in templates:
                if template_name in config.templates:
                    template = config.templates[template_name]
                    export_templates_dict[template_name] = {
                        "subject": template.subject,
                        "body": template.body,
                        "attachments": template.attachments,
                    }
                else:
                    console.print(f"[yellow]Warning:[/yellow] Template '{template_name}' not found")
        else:
            # Export all templates
            export_templates_dict = {}
            for name, template in config.templates.items():
                export_templates_dict[name] = {
                    "subject": template.subject,
                    "body": template.body,
                    "attachments": template.attachments,
                }

        if not export_templates_dict:
            console.print("[yellow]Warning:[/yellow] No templates selected for export.")
            return

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Export templates
        if export_format == "json":
            import json

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_templates_dict, f, indent=2, ensure_ascii=False)
        else:  # yaml
            import yaml

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    export_templates_dict, f, default_flow_style=False, indent=2, allow_unicode=True
                )

        console.print(
            f"[green]✓[/green] Exported {len(export_templates_dict)} templates to {file_path}"
        )

    except Exception as e:
        Logger.exception("Failed to export templates")
        console.print(f"[red]Error:[/red] Failed to export templates: {e}")
        raise click.Abort() from e


def _suggest_templates(available_templates: list[str]):
    """Suggest available templates when template not found."""
    if available_templates:
        console.print(f"Available templates: {', '.join(available_templates)}")
    else:
        console.print("No templates available. Create one with 'email-sender template create'")


# Make template_command the default export
__all__ = ["template_command"]
