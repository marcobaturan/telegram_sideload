# Gmail Bot Plugin

**Author:** Marco Baturan

## Overview

This plugin enables email-based conversations with your AI sideload through Gmail. Users can send emails with a specific subject trigger to have epistolary (letter-based) conversations with the bot.

## Features

- **OAuth 2.0 Authentication**: Secure Gmail API access
- **Email Monitoring**: Polls Gmail for trigger emails
- **Conversation Threading**: Maintains context within email threads
- **Security**: Whitelist-based sender validation
- **Parallel Operation**: Runs independently alongside Telegram bot
- **Shared AI Pipeline**: Uses the same workers and mindfile as Telegram

## How It Works

1. User sends email with subject "SIDELOAD-MESSAGE"
2. Plugin detects and validates the email
3. Message is processed through the AI pipeline
4. Bot sends reply via email
5. Conversation context is maintained in the thread

## Setup

### Prerequisites

- Google Cloud account
- Gmail API enabled
- OAuth 2.0 credentials

### Step-by-Step Setup

See the comprehensive setup guide: [Gmail Setup Guide](../../docs/gmail_setup.md)

Quick summary:
1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to plugin directory
5. Configure environment variables
6. Run first-time authentication

### Environment Variables

```bash
# Gmail API Credentials
GMAIL_CREDENTIALS_FILE='plugins/gmail_bot/credentials.json'
GMAIL_TOKEN_FILE='plugins/gmail_bot/token.json'

# Email Trigger
GMAIL_SUBJECT_TRIGGER='SIDELOAD-MESSAGE'

# Security (comma-separated)
ALLOWED_SENDER_EMAILS='your-email@gmail.com,another@example.com'

# Polling Configuration
GMAIL_POLL_INTERVAL_SECONDS='30'
```

## Usage

### Starting the Gmail Bot

```bash
# From project root
python3 plugins/gmail_bot/main_gmail.py
```

### Running Alongside Telegram

```bash
# Terminal 1 - Telegram bot
python3 main.py

# Terminal 2 - Gmail bot
python3 plugins/gmail_bot/main_gmail.py
```

### Sending an Email

**Subject:** `SIDELOAD-MESSAGE`  
**Body:** Your message or question

The bot will reply within the configured polling interval (default: 30 seconds).

### Continuing Conversations

Simply reply to the bot's email. The conversation context is maintained within the email thread.

## Configuration

All configuration is in `gmail_config.py`:

- **Credentials**: OAuth file paths
- **Trigger Subject**: Email subject to monitor
- **Security**: Allowed sender emails
- **Polling**: Check interval
- **Rate Limiting**: API quota management
- **Conversation Expiration**: 24 hours default

## Architecture

### Files

- `gmail_config.py` - Configuration settings
- `gmail_service.py` - Gmail API service
- `gmail_conversation_manager.py` - Conversation state management
- `main_gmail.py` - Main entry point
- `test_gmail_service.py` - Unit tests

### Integration

The plugin integrates with the existing framework through:
- `app_logic.py` - New `process_email_message()` method
- Shared worker pipeline (DoormanWorker, IntegrationWorker, etc.)
- Shared mindfile and AI providers

## Security

- **OAuth 2.0**: Secure Google authentication
- **Sender Whitelist**: Only processes emails from allowed addresses
- **Credential Protection**: `credentials.json` and `token.json` are gitignored
- **Rate Limiting**: Respects Gmail API quotas

## Testing

Run unit tests:
```bash
python -m pytest plugins/gmail_bot/test_gmail_service.py -v
```

## Troubleshooting

### "Credentials file not found"
- Ensure `credentials.json` is in `plugins/gmail_bot/`
- Check `GMAIL_CREDENTIALS_FILE` environment variable

### "Token has been expired or revoked"
- Delete `token.json`
- Run `main_gmail.py` again to re-authenticate

### Bot not detecting emails
- Verify email subject exactly matches trigger
- Check sender is in `ALLOWED_SENDER_EMAILS`
- Review console logs for errors

### Rate limit errors
- Increase `GMAIL_POLL_INTERVAL_SECONDS`
- Default quota: 250 units per user per second

## License

This plugin is released into the Public Domain under the Unlicense.

## Dependencies

See `requirements.txt` for Gmail API dependencies.
