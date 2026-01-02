"""
Gmail Conversation Manager

Manages conversation state for email-based interactions.
Maps Gmail thread IDs to conversation contexts.
"""

import time
from typing import Dict, List, Optional
from gmail_config import CONVERSATION_EXPIRATION_SECONDS


class GmailConversationManager:
    """
    Manages conversations for Gmail-based interactions.
    Similar to ConversationManager but adapted for email threading.
    """
    
    def __init__(self):
        """Initialize the Gmail conversation manager."""
        self._conversations: Dict[str, Dict] = {}
        # Structure: {
        #     "thread_id": {
        #         "messages": [...],
        #         "last_activity": timestamp,
        #         "sender_email": "user@example.com"
        #     }
        # }
    
    def get_conversation(self, thread_id: str) -> List[Dict]:
        """
        Get conversation history for a Gmail thread.
        
        Args:
            thread_id: Gmail thread ID
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        if thread_id not in self._conversations:
            return []
        
        # Check if conversation has expired
        conversation = self._conversations[thread_id]
        last_activity = conversation.get("last_activity", 0)
        
        if time.time() - last_activity > CONVERSATION_EXPIRATION_SECONDS:
            print(f"Conversation {thread_id} has expired, clearing history")
            self._conversations.pop(thread_id)
            return []
        
        return conversation.get("messages", [])
    
    def add_message(self, thread_id: str, role: str, content: str, sender_email: Optional[str] = None):
        """
        Add a message to the conversation history.
        
        Args:
            thread_id: Gmail thread ID
            role: Message role ('user' or 'assistant')
            content: Message content
            sender_email: Email address of the sender (for user messages)
        """
        if thread_id not in self._conversations:
            self._conversations[thread_id] = {
                "messages": [],
                "last_activity": time.time(),
                "sender_email": sender_email
            }
        
        conversation = self._conversations[thread_id]
        conversation["messages"].append({
            "role": role,
            "content": content
        })
        conversation["last_activity"] = time.time()
        
        if sender_email and role == "user":
            conversation["sender_email"] = sender_email
    
    def get_sender_email(self, thread_id: str) -> Optional[str]:
        """
        Get the sender email for a thread.
        
        Args:
            thread_id: Gmail thread ID
            
        Returns:
            Sender email address or None
        """
        if thread_id in self._conversations:
            return self._conversations[thread_id].get("sender_email")
        return None
    
    def clear_conversation(self, thread_id: str):
        """
        Clear conversation history for a thread.
        
        Args:
            thread_id: Gmail thread ID
        """
        if thread_id in self._conversations:
            self._conversations.pop(thread_id)
            print(f"Cleared conversation for thread {thread_id}")
    
    def get_all_thread_ids(self) -> List[str]:
        """
        Get all active thread IDs.
        
        Returns:
            List of thread IDs
        """
        return list(self._conversations.keys())
    
    def cleanup_expired_conversations(self):
        """
        Remove expired conversations from memory.
        Should be called periodically.
        """
        current_time = time.time()
        expired_threads = []
        
        for thread_id, conversation in self._conversations.items():
            last_activity = conversation.get("last_activity", 0)
            if current_time - last_activity > CONVERSATION_EXPIRATION_SECONDS:
                expired_threads.append(thread_id)
        
        for thread_id in expired_threads:
            self._conversations.pop(thread_id)
            print(f"Cleaned up expired conversation: {thread_id}")
        
        if expired_threads:
            print(f"Cleaned up {len(expired_threads)} expired conversation(s)")
    
    def get_conversation_count(self) -> int:
        """
        Get the number of active conversations.
        
        Returns:
            Number of active conversations
        """
        return len(self._conversations)
