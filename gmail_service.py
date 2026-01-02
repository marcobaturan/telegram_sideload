"""
Gmail Service

Handles Gmail API authentication, email monitoring, and sending responses.
"""

import os
import base64
import time
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    GMAIL_SCOPES,
    EMAIL_SUBJECT_TRIGGER,
    ALLOWED_SENDER_EMAILS,
    MAX_EMAIL_CONTENT_LENGTH,
    EMAIL_RESPONSE_TEMPLATE,
    GMAIL_SERVICE_LOG_PREFIX,
    MAX_EMAILS_PER_POLL
)


class GmailService:
    """
    Service for interacting with Gmail API.
    Handles authentication, email monitoring, and sending responses.
    """
    
    def __init__(self):
        """Initialize the Gmail service."""
        self.service = None
        self.user_id = 'me'
        self._processed_message_ids = set()  # Track processed messages to avoid duplicates
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Returns:
            True if authentication successful, False otherwise
        """
        creds = None
        
        # Check if token file exists
        if os.path.exists(GMAIL_TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
            except Exception as e:
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Error loading token: {e}")
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Refreshing access token...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} ERROR: Credentials file not found: {GMAIL_CREDENTIALS_FILE}")
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Please follow the setup instructions in docs/gmail_setup.md")
                    return False
                
                try:
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Starting OAuth flow...")
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} A browser window will open for authentication.")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Error during OAuth flow: {e}")
                    return False
            
            # Save credentials for next run
            try:
                with open(GMAIL_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Credentials saved to {GMAIL_TOKEN_FILE}")
            except Exception as e:
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Warning: Could not save token: {e}")
        
        # Build the service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Successfully authenticated with Gmail API")
            return True
        except Exception as e:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error building Gmail service: {e}")
            return False
    
    def get_unread_trigger_emails(self) -> List[Dict[str, Any]]:
        """
        Get unread emails with the trigger subject.
        
        Returns:
            List of email dictionaries with thread_id, message_id, sender, subject, body
        """
        if not self.service:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Service not authenticated")
            return []
        
        try:
            # Search for unread emails with the trigger subject
            query = f'is:unread subject:"{EMAIL_SUBJECT_TRIGGER}"'
            results = self.service.users().messages().list(
                userId=self.user_id,
                q=query,
                maxResults=MAX_EMAILS_PER_POLL
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Found {len(messages)} unread trigger email(s)")
            
            emails = []
            for msg in messages:
                msg_id = msg['id']
                
                # Skip if already processed
                if msg_id in self._processed_message_ids:
                    continue
                
                # Get full message details
                message = self.service.users().messages().get(
                    userId=self.user_id,
                    id=msg_id,
                    format='full'
                ).execute()
                
                # Extract email details
                email_data = self._parse_email(message)
                if email_data:
                    emails.append(email_data)
                    self._processed_message_ids.add(msg_id)
            
            return emails
            
        except HttpError as error:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error fetching emails: {error}")
            return []
    
    def _parse_email(self, message: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse Gmail message into structured format.
        
        Args:
            message: Gmail API message object
            
        Returns:
            Dictionary with email details or None if parsing fails
        """
        try:
            headers = message['payload']['headers']
            
            # Extract headers
            sender = None
            subject = None
            for header in headers:
                if header['name'].lower() == 'from':
                    sender = header['value']
                elif header['name'].lower() == 'subject':
                    subject = header['value']
            
            # Extract sender email address
            sender_email = self._extract_email_address(sender)
            
            # Check if sender is allowed
            if ALLOWED_SENDER_EMAILS and sender_email not in ALLOWED_SENDER_EMAILS:
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Ignoring email from unauthorized sender: {sender_email}")
                return None
            
            # Extract body
            body = self._get_email_body(message['payload'])
            
            if not body:
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Warning: Empty email body")
                body = ""
            
            # Truncate if too long
            if len(body) > MAX_EMAIL_CONTENT_LENGTH:
                body = body[:MAX_EMAIL_CONTENT_LENGTH]
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Truncated email body to {MAX_EMAIL_CONTENT_LENGTH} chars")
            
            return {
                'message_id': message['id'],
                'thread_id': message['threadId'],
                'sender': sender,
                'sender_email': sender_email,
                'subject': subject,
                'body': body
            }
            
        except Exception as e:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error parsing email: {e}")
            return None
    
    def _extract_email_address(self, from_header: str) -> str:
        """
        Extract email address from 'From' header.
        
        Args:
            from_header: From header value (e.g., "Name <email@example.com>")
            
        Returns:
            Email address
        """
        if '<' in from_header and '>' in from_header:
            start = from_header.index('<') + 1
            end = from_header.index('>')
            return from_header[start:end].strip().lower()
        return from_header.strip().lower()
    
    def _get_email_body(self, payload: Dict) -> str:
        """
        Extract email body from payload.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Email body text
        """
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        # Simple HTML tag removal
                        import re
                        body = re.sub('<[^<]+?>', '', body)
        else:
            # Simple message
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body.strip()
    
    def send_reply(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email reply.
        
        Args:
            thread_id: Gmail thread ID to reply to
            to_email: Recipient email address
            subject: Email subject (will be prefixed with Re: if not already)
            body: Email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.service:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Service not authenticated")
            return False
        
        try:
            # Format the response using template
            formatted_body = EMAIL_RESPONSE_TEMPLATE.format(response=body)
            
            # Ensure subject has Re: prefix for replies
            if not subject.startswith('Re:'):
                subject = f'Re: {subject}'
            
            # Create message
            message = MIMEText(formatted_body)
            message['to'] = to_email
            message['subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = {
                'raw': raw_message,
                'threadId': thread_id
            }
            
            self.service.users().messages().send(
                userId=self.user_id,
                body=send_message
            ).execute()
            
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Successfully sent reply to {to_email}")
            return True
            
        except HttpError as error:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error sending email: {error}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error marking email as read: {error}")
            return False
