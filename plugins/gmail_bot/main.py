"""
Gmail Bot Plugin - Main Entry Point

This plugin is NOT a message preprocessor like other plugins.
It's a standalone service that runs independently to monitor Gmail.

This file is kept for compatibility but the actual entry point is main_gmail.py
"""

def is_plugin_applicable(messages, provider):
    """
    This plugin doesn't process Telegram messages.
    It runs as a separate service.
    
    Returns:
        False - This plugin is not applicable to message processing
    """
    return False


def process_messages(messages, provider):
    """
    This plugin doesn't modify messages.
    
    Returns:
        messages - Unmodified messages
    """
    return messages
