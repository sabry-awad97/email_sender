# Email Sender CLI

A robust, modular, and reusable command-line interface (CLI) application for sending emails with attachments. Built with clean architecture principles and comprehensive configuration management.

## Features

- 🚀 **Easy to Use**: Simple CLI commands for sending emails
- 📎 **Attachment Support**: Send any file type with automatic MIME type detection
- 📧 **Bulk Sending**: Send emails to multiple recipients from a file
- 🎨 **Templates**: Create and manage reusable email templates
- ⚙️ **Flexible Configuration**: YAML configuration files with environment variable support
- 🔒 **Secure**: Support for app passwords and TLS/SSL encryption
- 📊 **Rich Output**: Beautiful terminal output with progress indicators
- 🛠️ **Extensible**: Clean architecture with dependency injection

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd email_sender

# Install dependencies
pip install -e .

# Or using uv (recommended)
uv sync
```

### Using pip (when published)

```bash
pip install email-sender
```

## Quick Start

### 1. Initialize Configuration

```bash
# Interactive setup
email-sender config init --interactive

# Or create default config and edit manually
email-sender config init
```

### 2. Send Your First Email

```bash
# Simple email
email-sender send single --to recipient@example.com --subject "Hello" --body "World"

# With attachment
email-sender send single --to user@example.com --subject "Report" --attach report.pdf

# Interactive mode
email-sender send single --interactive
```

## Configuration

The CLI uses YAML configuration files for maximum flexibility. Configuration is loaded from:

1. `~/.email-sender/config.yaml` (user config)
2. `./config.yaml` (project config)
3. `./.email-sender.yaml` (project config)
4. Environment variables (with `EMAIL_SENDER_` prefix)

### Example Configuration

```yaml
smtp:
  server: smtp.gmail.com
  port: 465
  use_tls: true
  username: your-email@gmail.com
  password: your-app-password

default_sender: your-email@gmail.com

logging:
  level: INFO
  console: true
  file: email-sender.log

templates:
  welcome:
    name: welcome
    subject: Welcome to Our Service!
    body: |
      Hello and welcome!

      We're excited to have you on board.

      Best regards,
      The Team
    attachments: []

attachment_max_size: 26214400 # 25MB
```

### Environment Variables

Override configuration using environment variables:

```bash
export EMAIL_SENDER_SMTP_SERVER=smtp.gmail.com
export EMAIL_SENDER_SMTP_PORT=465
export EMAIL_SENDER_SMTP_USERNAME=your-email@gmail.com
export EMAIL_SENDER_SMTP_PASSWORD=your-app-password
export EMAIL_SENDER_DEFAULT_SENDER=your-email@gmail.com
export EMAIL_SENDER_LOG_LEVEL=DEBUG
```

## Commands

### Configuration Management

```bash
# Initialize configuration
email-sender config init [--interactive] [--path CONFIG_PATH]

# Show current configuration
email-sender config show [--section SECTION] [--format yaml|table]

# Set configuration values
email-sender config set smtp.server smtp.gmail.com
email-sender config set smtp.port 587 --type int
email-sender config set smtp.use_tls true --type bool

# Validate configuration and test SMTP connection
email-sender config validate

# Show configuration file path
email-sender config path
```

### Sending Emails

#### Single Email

```bash
# Basic usage
email-sender send single --to recipient@example.com --subject "Subject" --body "Message"

# With multiple recipients
email-sender send single --to user1@example.com --to user2@example.com --subject "Subject"

# With attachments
email-sender send single --to user@example.com --subject "Report" --attach report.pdf --attach data.xlsx

# Using template
email-sender send single --to user@example.com --template welcome

# From file
email-sender send single --to user@example.com --subject "Report" --body-file message.txt

# Custom sender
email-sender send single --to user@example.com --subject "Test" --from custom@example.com

# Dry run (preview without sending)
email-sender send single --to user@example.com --subject "Test" --dry-run

# Interactive mode
email-sender send single --interactive
```

#### Bulk Email

```bash
# Send to recipients from file
email-sender send bulk --recipients-file emails.txt --subject "Newsletter" --body "Content"

# With template and delay
email-sender send bulk --recipients-file emails.txt --template newsletter --delay 2.0

# Dry run
email-sender send bulk --recipients-file emails.txt --template newsletter --dry-run
```

Recipients file format (one email per line):

```
user1@example.com
user2@example.com
# Comments are ignored
user3@example.com
```

### Template Management

```bash
# List all templates
email-sender template list

# Show template details
email-sender template show TEMPLATE_NAME

# Create new template
email-sender template create welcome --subject "Welcome!" --body "Welcome message"

# Interactive template creation
email-sender template create newsletter --interactive

# Create from file
email-sender template create report --subject "Monthly Report" --body-file template.txt

# Edit existing template
email-sender template edit welcome --subject "New Welcome Message"

# Copy template
email-sender template copy welcome welcome-v2

# Delete template
email-sender template delete old-template
```

### General Commands

```bash
# Show version
email-sender version

# Show application status
email-sender status

# Get help
email-sender --help
email-sender COMMAND --help
```

## SMTP Provider Setup

### Gmail

1. Enable 2-Factor Authentication
2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use the app password in your configuration

```yaml
smtp:
  server: smtp.gmail.com
  port: 465
  use_tls: true
  username: your-email@gmail.com
  password: your-16-char-app-password
```

### Outlook/Hotmail

```yaml
smtp:
  server: smtp-mail.outlook.com
  port: 587
  use_tls: true
  username: your-email@outlook.com
  password: your-password
```

### Yahoo

```yaml
smtp:
  server: smtp.mail.yahoo.com
  port: 465
  use_tls: true
  username: your-email@yahoo.com
  password: your-app-password
```

## Examples

### Send Welcome Email with Template

```bash
# Create template
email-sender template create welcome \
  --subject "Welcome to Our Service!" \
  --body "Hello! Welcome to our amazing service. We're glad to have you!"

# Send using template
email-sender send single --to newuser@example.com --template welcome
```

### Bulk Newsletter

```bash
# Create recipients file
echo -e "user1@example.com\nuser2@example.com\nuser3@example.com" > subscribers.txt

# Create newsletter template
email-sender template create newsletter \
  --subject "Monthly Newsletter - $(date +%B)" \
  --body-file newsletter-content.txt \
  --attach newsletter.pdf

# Send to all subscribers
email-sender send bulk --recipients-file subscribers.txt --template newsletter --delay 1.0
```

### Report with Multiple Attachments

```bash
email-sender send single \
  --to manager@company.com \
  --subject "Weekly Report - $(date +%Y-%m-%d)" \
  --body "Please find attached this week's reports." \
  --attach sales-report.pdf \
  --attach analytics-data.xlsx \
  --attach summary.docx
```

## Architecture

The application follows clean architecture principles:

```
├── cli/                    # CLI interface layer
│   ├── main.py            # Main CLI entry point
│   └── commands/          # Command implementations
├── config/                # Configuration management
│   ├── schema.py          # Configuration schema
│   └── manager.py         # Configuration manager
├── core/                  # Business logic
│   ├── email_service.py   # Email service
│   ├── attachment.py      # Attachment handling
│   └── interfaces.py      # Abstract interfaces
├── infrastructure/        # External services
│   ├── smtp_client.py     # SMTP implementation
│   └── logger.py          # Logging service
└── models/               # Data models
    └── email_message.py   # Email message model
```

## Error Handling

The CLI provides comprehensive error handling with helpful messages:

- **Configuration errors**: Clear guidance on fixing config issues
- **SMTP errors**: Specific error messages for connection/authentication problems
- **File errors**: Helpful messages for missing or invalid files
- **Validation errors**: Detailed validation error messages

## Logging

Configurable logging with multiple levels and outputs:

- **Console logging**: Rich formatted output with colors
- **File logging**: Standard format for log files
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Security Best Practices

- **App Passwords**: Use app-specific passwords instead of account passwords
- **Environment Variables**: Store sensitive data in environment variables
- **TLS/SSL**: Encrypted connections to SMTP servers
- **Configuration Files**: Keep config files secure and out of version control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:

- Create an issue on GitHub
- Check the documentation
- Use `email-sender --help` for command help
