"""
Gmail Service Configuration

This module contains all configuration settings for the Gmail integration.
"""

import os

# Gmail API Settings
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "plugins/gmail_bot/credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "plugins/gmail_bot/token.json")

# Gmail API Scopes
# We need to read emails and send emails
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'  # For marking emails as read
]

# Email Trigger Configuration
EMAIL_SUBJECT_TRIGGER = os.getenv("GMAIL_SUBJECT_TRIGGER", "SIDELOAD-MESSAGE")

# Security: Allowed sender emails (comma-separated in env var)
ALLOWED_SENDER_EMAILS_STR = os.getenv("ALLOWED_SENDER_EMAILS", "")
ALLOWED_SENDER_EMAILS = [
    email.strip() 
    for email in ALLOWED_SENDER_EMAILS_STR.split(",") 
    if email.strip()
]

# Polling Configuration
GMAIL_POLL_INTERVAL_SECONDS = int(os.getenv("GMAIL_POLL_INTERVAL_SECONDS", "30"))

# Email Length Limits
MAX_EMAIL_CONTENT_LENGTH = 50000  # Maximum characters to process from incoming email
MAX_EMAIL_RESPONSE_LENGTH = 10000  # Maximum characters in bot response

# Email Response Formatting
EMAIL_RESPONSE_TEMPLATE = """
{response}

---
This is an automated response from your AI sideload.
To continue the conversation, reply to this email.
"""

# Email-specific prompt addition
EMAIL_SPECIFIC_PROMPT = """
Note: This is an email conversation, not instant messaging.
- Responses can be more detailed and formal than in IM
- Use proper email etiquette
- Structure longer responses with paragraphs
- You can be more comprehensive since email allows for longer messages
"""

# Conversation expiration (in seconds)
# After this time of inactivity, conversation context may be cleared
CONVERSATION_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

# Logging
GMAIL_SERVICE_LOG_PREFIX = "[Gmail Service]"

# Rate limiting
MAX_EMAILS_PER_POLL = 10  # Maximum number of emails to process in one poll cycle
