"""
Unit tests for Gmail Service

These tests use mocked Gmail API responses to verify the service functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import base64
from gmail_service import GmailService


class TestGmailService(unittest.TestCase):
    """Test cases for GmailService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gmail_service = GmailService()
    
    @patch('gmail_service.os.path.exists')
    @patch('gmail_service.build')
    @patch('gmail_service.Credentials.from_authorized_user_file')
    def test_authenticate_with_existing_token(self, mock_creds, mock_build, mock_exists):
        """Test authentication with existing valid token."""
        # Mock existing token file
        mock_exists.return_value = True
        
        # Mock valid credentials
        mock_cred_instance = Mock()
        mock_cred_instance.valid = True
        mock_creds.return_value = mock_cred_instance
        
        # Mock Gmail service build
        mock_build.return_value = Mock()
        
        # Test authentication
        result = self.gmail_service.authenticate()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.gmail_service.service)
    
    def test_extract_email_address(self):
        """Test email address extraction from From header."""
        # Test with name and email
        from_header = "John Doe <john@example.com>"
        result = self.gmail_service._extract_email_address(from_header)
        self.assertEqual(result, "john@example.com")
        
        # Test with email only
        from_header = "jane@example.com"
        result = self.gmail_service._extract_email_address(from_header)
        self.assertEqual(result, "jane@example.com")
        
        # Test with complex name
        from_header = "Dr. Jane Smith, PhD <jane.smith@university.edu>"
        result = self.gmail_service._extract_email_address(from_header)
        self.assertEqual(result, "jane.smith@university.edu")
    
    def test_get_email_body_simple(self):
        """Test email body extraction from simple message."""
        # Create mock payload for plain text email
        test_body = "Hello, this is a test email."
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')
        
        payload = {
            'body': {
                'data': encoded_body
            }
        }
        
        result = self.gmail_service._get_email_body(payload)
        self.assertEqual(result, test_body)
    
    def test_get_email_body_multipart(self):
        """Test email body extraction from multipart message."""
        # Create mock payload for multipart email
        test_body = "This is the plain text part."
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')
        
        payload = {
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': encoded_body
                    }
                },
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': base64.urlsafe_b64encode(b'<html>HTML part</html>').decode('utf-8')
                    }
                }
            ]
        }
        
        result = self.gmail_service._get_email_body(payload)
        self.assertEqual(result, test_body)
    
    @patch.object(GmailService, 'service')
    def test_parse_email(self, mock_service):
        """Test email parsing."""
        # Create mock email message
        test_body = "Test email body"
        encoded_body = base64.urlsafe_b64encode(test_body.encode('utf-8')).decode('utf-8')
        
        message = {
            'id': 'msg123',
            'threadId': 'thread456',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'Test User <test@example.com>'},
                    {'name': 'Subject', 'value': 'SIDELOAD-MESSAGE'}
                ],
                'body': {
                    'data': encoded_body
                }
            }
        }
        
        # Mock allowed senders (need to patch the config)
        with patch('gmail_service.ALLOWED_SENDER_EMAILS', ['test@example.com']):
            result = self.gmail_service._parse_email(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['message_id'], 'msg123')
        self.assertEqual(result['thread_id'], 'thread456')
        self.assertEqual(result['sender_email'], 'test@example.com')
        self.assertEqual(result['subject'], 'SIDELOAD-MESSAGE')
        self.assertEqual(result['body'], test_body)
    
    @patch.object(GmailService, 'service')
    def test_parse_email_unauthorized_sender(self, mock_service):
        """Test that emails from unauthorized senders are rejected."""
        message = {
            'id': 'msg123',
            'threadId': 'thread456',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'Unauthorized <bad@example.com>'},
                    {'name': 'Subject', 'value': 'SIDELOAD-MESSAGE'}
                ],
                'body': {
                    'data': base64.urlsafe_b64encode(b'Test').decode('utf-8')
                }
            }
        }
        
        # Mock allowed senders
        with patch('gmail_service.ALLOWED_SENDER_EMAILS', ['allowed@example.com']):
            result = self.gmail_service._parse_email(message)
        
        self.assertIsNone(result)


class TestGmailConversationManager(unittest.TestCase):
    """Test cases for GmailConversationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from gmail_conversation_manager import GmailConversationManager
        self.manager = GmailConversationManager()
    
    def test_add_and_get_message(self):
        """Test adding and retrieving messages."""
        thread_id = "thread123"
        
        # Add user message
        self.manager.add_message(thread_id, "user", "Hello bot", "user@example.com")
        
        # Get conversation
        messages = self.manager.get_conversation(thread_id)
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[0]['content'], 'Hello bot')
    
    def test_conversation_threading(self):
        """Test that conversations are properly threaded."""
        thread1 = "thread1"
        thread2 = "thread2"
        
        # Add messages to different threads
        self.manager.add_message(thread1, "user", "Message in thread 1", "user1@example.com")
        self.manager.add_message(thread2, "user", "Message in thread 2", "user2@example.com")
        self.manager.add_message(thread1, "assistant", "Response in thread 1")
        
        # Verify thread separation
        thread1_msgs = self.manager.get_conversation(thread1)
        thread2_msgs = self.manager.get_conversation(thread2)
        
        self.assertEqual(len(thread1_msgs), 2)
        self.assertEqual(len(thread2_msgs), 1)
    
    def test_get_sender_email(self):
        """Test retrieving sender email for a thread."""
        thread_id = "thread123"
        sender_email = "test@example.com"
        
        self.manager.add_message(thread_id, "user", "Test message", sender_email)
        
        retrieved_email = self.manager.get_sender_email(thread_id)
        self.assertEqual(retrieved_email, sender_email)
    
    def test_clear_conversation(self):
        """Test clearing a conversation."""
        thread_id = "thread123"
        
        # Add messages
        self.manager.add_message(thread_id, "user", "Message 1", "user@example.com")
        self.manager.add_message(thread_id, "assistant", "Response 1")
        
        # Clear conversation
        self.manager.clear_conversation(thread_id)
        
        # Verify cleared
        messages = self.manager.get_conversation(thread_id)
        self.assertEqual(len(messages), 0)


if __name__ == '__main__':
    unittest.main()
