#!/usr/bin/env python3
"""
Gmail Bot Main Entry Point

This is the main entry point for the Gmail-based sideload bot.
It runs independently from the Telegram bot but shares the same AI pipeline.

Usage:
    python3 main_gmail.py

Setup:
    See docs/gmail_setup.md for detailed setup instructions.
"""

import asyncio
import time
import signal
import sys

from gmail_service import GmailService
from gmail_conversation_manager import GmailConversationManager
from gmail_config import (
    GMAIL_POLL_INTERVAL_SECONDS,
    GMAIL_SERVICE_LOG_PREFIX,
    EMAIL_SPECIFIC_PROMPT
)
from app_logic import AppLogic
from conversation_manager import ConversationManager
from bot_config import get_allowed_user_ids, get_allowed_group_ids


class GmailBot:
    """
    Gmail bot that monitors emails and responds using the AI pipeline.
    """
    
    def __init__(self):
        """Initialize the Gmail bot."""
        self.gmail_service = GmailService()
        self.gmail_conversation_manager = GmailConversationManager()
        
        # Initialize shared components (same as Telegram bot)
        telegram_conversation_manager = ConversationManager()
        allowed_user_ids = get_allowed_user_ids()
        allowed_group_ids = get_allowed_group_ids()
        
        self.app_logic = AppLogic(
            conversation_manager=telegram_conversation_manager,
            allowed_user_ids=allowed_user_ids,
            allowed_group_ids=allowed_group_ids
        )
        
        self.running = False
        self.cleanup_counter = 0
    
    def start(self) -> bool:
        """
        Start the Gmail bot.
        
        Returns:
            True if started successfully, False otherwise
        """
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Starting Gmail Bot...")
        
        # Authenticate with Gmail
        if not self.gmail_service.authenticate():
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Failed to authenticate. Exiting.")
            return False
        
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Gmail Bot started successfully!")
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Monitoring emails with subject trigger...")
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Poll interval: {GMAIL_POLL_INTERVAL_SECONDS} seconds")
        
        self.running = True
        return True
    
    def stop(self):
        """Stop the Gmail bot."""
        print(f"\n{GMAIL_SERVICE_LOG_PREFIX} Stopping Gmail Bot...")
        self.running = False
    
    def process_emails(self):
        """
        Check for new emails and process them.
        This is the main processing loop.
        """
        try:
            # Get unread trigger emails
            emails = self.gmail_service.get_unread_trigger_emails()
            
            if not emails:
                return
            
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Processing {len(emails)} email(s)...")
            
            for email_data in emails:
                try:
                    self._process_single_email(email_data)
                except Exception as e:
                    print(f"{GMAIL_SERVICE_LOG_PREFIX} Error processing email: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Periodic cleanup of expired conversations
            self.cleanup_counter += 1
            if self.cleanup_counter >= 10:  # Every 10 poll cycles
                self.gmail_conversation_manager.cleanup_expired_conversations()
                self.cleanup_counter = 0
                
        except Exception as e:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error in process_emails: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_single_email(self, email_data: dict):
        """
        Process a single email and send response.
        
        Args:
            email_data: Dictionary with email details
        """
        message_id = email_data['message_id']
        thread_id = email_data['thread_id']
        sender_email = email_data['sender_email']
        subject = email_data['subject']
        body = email_data['body']
        
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Processing email from {sender_email}")
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Thread ID: {thread_id}")
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Subject: {subject}")
        
        try:
            # Generate AI response using app logic
            ai_response = self.app_logic.process_email_message(
                sender_email=sender_email,
                thread_id=thread_id,
                email_body=body,
                conversation_manager=self.gmail_conversation_manager
            )
            
            # Send reply
            success = self.gmail_service.send_reply(
                thread_id=thread_id,
                to_email=sender_email,
                subject=subject,
                body=ai_response
            )
            
            if success:
                # Mark original email as read
                self.gmail_service.mark_as_read(message_id)
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Successfully processed and replied to email")
            else:
                print(f"{GMAIL_SERVICE_LOG_PREFIX} Failed to send reply")
                
        except Exception as e:
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Error generating response: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """
        Main run loop for the Gmail bot.
        """
        if not self.start():
            return
        
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Entering main loop...")
        print(f"{GMAIL_SERVICE_LOG_PREFIX} Press Ctrl+C to stop")
        
        try:
            while self.running:
                self.process_emails()
                time.sleep(GMAIL_POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print(f"\n{GMAIL_SERVICE_LOG_PREFIX} Received interrupt signal")
        finally:
            self.stop()
            print(f"{GMAIL_SERVICE_LOG_PREFIX} Gmail Bot stopped")


def signal_handler(sig, frame):
    """Handle interrupt signals gracefully."""
    print(f"\n{GMAIL_SERVICE_LOG_PREFIX} Interrupt received, shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run bot
    bot = GmailBot()
    bot.run()


if __name__ == "__main__":
    main()
