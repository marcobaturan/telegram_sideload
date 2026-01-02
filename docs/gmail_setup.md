# Gmail Integration Setup Guide

This guide walks you through setting up Gmail API integration for the Telegram Sideload Bot.

## Prerequisites

- Python 3.8 or higher
- A Google account
- Access to Google Cloud Console

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Telegram Sideload Gmail Bot")
4. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and then click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: Select "External" (unless you have a Google Workspace)
   - Click "Create"
   - Fill in required fields:
     - App name: "Telegram Sideload Gmail Bot"
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Skip "Scopes" (click "Save and Continue")
   - Add your email as a test user
   - Click "Save and Continue"
4. Back to "Create OAuth client ID":
   - Application type: Select "Desktop app"
   - Name: "Gmail Bot Desktop Client"
   - Click "Create"
5. Download the credentials:
   - Click the download button (⬇️) next to your newly created OAuth 2.0 Client ID
   - Save the file as `credentials.json` in your project root directory

## Step 4: Configure Environment Variables

Add the following to your environment variables (or `.env` file):

```bash
# Gmail Configuration
GMAIL_CREDENTIALS_FILE='credentials.json'  # Path to your credentials file
GMAIL_TOKEN_FILE='token.json'              # Where to store the auth token
GMAIL_SUBJECT_TRIGGER='SIDELOAD-MESSAGE'   # Email subject to trigger bot
GMAIL_POLL_INTERVAL_SECONDS='30'           # How often to check for emails

# Security: Allowed sender emails (comma-separated)
ALLOWED_SENDER_EMAILS='your-email@gmail.com,another-email@example.com'
```

**Important**: Replace `your-email@gmail.com` with the actual email addresses you want to allow.

## Step 5: Install Dependencies

```bash
cd /path/to/telegram_sideload
pip install -r requirements.txt
```

## Step 6: First Run - OAuth Authentication

1. Run the Gmail bot for the first time:
   ```bash
   python3 main_gmail.py
   ```

2. A browser window will automatically open
3. Sign in with your Google account
4. You'll see a warning "Google hasn't verified this app"
   - Click "Advanced"
   - Click "Go to [Your App Name] (unsafe)"
   - This is safe because it's your own app
5. Grant the requested permissions:
   - Read emails
   - Send emails
   - Modify emails (mark as read)
6. The browser will show "The authentication flow has completed"
7. Return to your terminal - the bot should now be running

A `token.json` file will be created in your project directory. This stores your authentication token for future runs.

## Step 7: Test the Integration

1. Send an email to your Gmail account with:
   - **Subject**: `SIDELOAD-MESSAGE`
   - **Body**: Any message or question

2. Wait up to 30 seconds (default polling interval)

3. Check your inbox for the bot's reply

4. Reply to the bot's email to continue the conversation

## Running Both Services

You can run both Telegram and Gmail bots simultaneously:

**Terminal 1 - Telegram Bot:**
```bash
python3 main.py
```

**Terminal 2 - Gmail Bot:**
```bash
python3 main_gmail.py
```

Both services will share the same AI pipeline and mindfile.

## Security Best Practices

1. **Keep credentials secure**:
   - Never commit `credentials.json` or `token.json` to version control
   - Add them to `.gitignore`

2. **Restrict sender emails**:
   - Always set `ALLOWED_SENDER_EMAILS` to specific addresses
   - Don't leave it empty in production

3. **OAuth consent screen**:
   - Keep your app in "Testing" mode if only you will use it
   - Only add trusted users as test users

## Troubleshooting

### "Credentials file not found"
- Ensure `credentials.json` is in the correct location
- Check the `GMAIL_CREDENTIALS_FILE` environment variable

### "Token has been expired or revoked"
- Delete `token.json`
- Run `python3 main_gmail.py` again to re-authenticate

### "Access blocked: This app's request is invalid"
- Make sure you've enabled the Gmail API in Google Cloud Console
- Verify your OAuth consent screen is properly configured

### Bot not detecting emails
- Check that the email subject exactly matches `SIDELOAD-MESSAGE`
- Verify the sender email is in `ALLOWED_SENDER_EMAILS`
- Check the console logs for errors

### Rate limit errors
- Increase `GMAIL_POLL_INTERVAL_SECONDS` to reduce API calls
- Default quota is 250 units per user per second (should be sufficient)

## Advanced Configuration

### Custom Subject Trigger

Change the trigger subject by setting:
```bash
GMAIL_SUBJECT_TRIGGER='MY-CUSTOM-TRIGGER'
```

### Polling Interval

Adjust how often the bot checks for emails:
```bash
GMAIL_POLL_INTERVAL_SECONDS='60'  # Check every 60 seconds
```

### Multiple Email Accounts

To monitor multiple Gmail accounts, run separate instances of `main_gmail.py` with different credentials files:

```bash
# Instance 1
GMAIL_CREDENTIALS_FILE='credentials1.json' GMAIL_TOKEN_FILE='token1.json' python3 main_gmail.py

# Instance 2
GMAIL_CREDENTIALS_FILE='credentials2.json' GMAIL_TOKEN_FILE='token2.json' python3 main_gmail.py
```

## Production Deployment

For production use with `tmux` or `screen`:

```bash
# Start Telegram bot
tmux new-session -d -s telegram_bot 'python3 main.py'

# Start Gmail bot
tmux new-session -d -s gmail_bot 'python3 main_gmail.py'

# List sessions
tmux ls

# Attach to a session
tmux attach -t gmail_bot
```

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify your Google Cloud Console configuration
3. Ensure all environment variables are set correctly
