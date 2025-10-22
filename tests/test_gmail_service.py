#!/usr/bin/env python3
"""
Unit tests for Gmail Service functionality.
Tests Gmail API integration, OAuth, and email operations.
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the Gmail service dependencies
with patch.dict('sys.modules', {
    'googleapiclient': Mock(),
    'googleapiclient.discovery': Mock(),
    'google.oauth2.credentials': Mock(),
    'google_auth_oauthlib.flow': Mock(),
    'google.auth.transport.requests': Mock()
}):
    from services.gmail_service import GmailService
    from utils.exception import CustomException


class TestGmailService(unittest.TestCase):
    """Test cases for Gmail Service functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the Gmail service to avoid actual API calls
        self.mock_service = Mock()
        self.mock_credentials = Mock()
        
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_gmail_service_initialization_with_existing_token(self, mock_exists, mock_creds, mock_build):
        """Test Gmail service initialization with existing token."""
        # Mock existing token file
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Initialize service
        gmail_service = GmailService()
        
        # Verify initialization
        self.assertIsNotNone(gmail_service.service)
        mock_creds.assert_called_once()
        mock_build.assert_called_once()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.InstalledAppFlow.from_client_secrets_file')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_gmail_service_initialization_without_token(self, mock_open, mock_exists, mock_creds, mock_flow, mock_build):
        """Test Gmail service initialization without existing token."""
        # Mock no existing token file
        mock_exists.return_value = False
        mock_creds.return_value = None
        mock_flow_instance = Mock()
        mock_flow.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        self.mock_credentials.to_json.return_value = '{"token": "mock_token"}'
        mock_build.return_value = self.mock_service
        
        # Initialize service
        gmail_service = GmailService()
        
        # Verify initialization
        self.assertIsNotNone(gmail_service.service)
        mock_flow.assert_called_once()
        mock_build.assert_called_once()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_fetch_emails_with_date_range(self, mock_exists, mock_creds, mock_build):
        """Test fetching emails with date range."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock email data
        mock_emails = [
            {
                "id": "email1",
                "sender": "test@example.com",
                "subject": "Test Email",
                "snippet": "Test content",
                "received": "2024-01-01T00:00:00Z",
                "labels": "INBOX"
            }
        ]
        
        # Mock Gmail API response
        mock_messages_list = Mock()
        mock_messages_list.execute.return_value = {
            "messages": [{"id": "email1"}]
        }
        
        mock_messages_get = Mock()
        mock_messages_get.execute.return_value = {
            "id": "email1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Subject", "value": "Test Email"}
                ]
            },
            "snippet": "Test content",
            "internalDate": "1704067200000",
            "labelIds": "INBOX"
        }
        
        self.mock_service.users.return_value.messages.return_value.list.return_value = mock_messages_list
        self.mock_service.users.return_value.messages.return_value.get.return_value = mock_messages_get
        
        # Initialize service and test
        gmail_service = GmailService()
        emails = gmail_service.fetch_emails(start_time=1704067200, end_time=1704153600)
        
        # Verify results
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]["id"], "email1")
        self.assertEqual(emails[0]["sender"], "test@example.com")
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_mark_as_read(self, mock_exists, mock_creds, mock_build):
        """Test marking email as read."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock Gmail API response
        mock_modify = Mock()
        mock_modify.execute.return_value = {"id": "email1"}
        self.mock_service.users.return_value.messages.return_value.modify.return_value = mock_modify
        
        # Initialize service and test
        gmail_service = GmailService()
        gmail_service.mark_as_read("email1")
        
        # Verify API call
        self.mock_service.users.return_value.messages.return_value.modify.assert_called_once()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_mark_as_unread(self, mock_exists, mock_creds, mock_build):
        """Test marking email as unread."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock Gmail API response
        mock_modify = Mock()
        mock_modify.execute.return_value = {"id": "email1"}
        self.mock_service.users.return_value.messages.return_value.modify.return_value = mock_modify
        
        # Initialize service and test
        gmail_service = GmailService()
        gmail_service.mark_as_unread("email1")
        
        # Verify API call
        self.mock_service.users.return_value.messages.return_value.modify.assert_called_once()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_create_label(self, mock_exists, mock_creds, mock_build):
        """Test creating a new label."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock Gmail API response
        mock_create = Mock()
        mock_create.execute.return_value = {
            "id": "label_123",
            "name": "Test Label"
        }
        self.mock_service.users.return_value.labels.return_value.create.return_value = mock_create
        
        # Initialize service and test
        gmail_service = GmailService()
        result = gmail_service.create_label("Test Label")
        
        # Verify results
        self.assertEqual(result["id"], "label_123")
        self.assertEqual(result["name"], "Test Label")
        self.mock_service.users.return_value.labels.return_value.create.assert_called_once()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_get_available_labels(self, mock_exists, mock_creds, mock_build):
        """Test getting available labels."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock Gmail API response
        mock_list = Mock()
        mock_list.execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX"},
                {"id": "SENT", "name": "SENT"},
                {"id": "label_123", "name": "Custom Label"}
            ]
        }
        self.mock_service.users.return_value.labels.return_value.list.return_value = mock_list
        
        # Initialize service and test
        gmail_service = GmailService()
        labels = gmail_service.get_available_labels()
        
        # Verify results
        self.assertEqual(len(labels), 3)
        self.assertIn("INBOX", labels)
        self.assertIn("SENT", labels)
        self.assertIn("Custom Label", labels)
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_move_message(self, mock_exists, mock_creds, mock_build):
        """Test moving message to different label."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock Gmail API response
        mock_modify = Mock()
        mock_modify.execute.return_value = {"id": "email1"}
        self.mock_service.users.return_value.messages.return_value.modify.return_value = mock_modify
        
        # Initialize service and test
        gmail_service = GmailService()
        mock_crud_service = Mock()
        mock_crud_service.get_labels_mapping.return_value = [{'id': 'label_123', 'name': 'Test Label'}]
        
        result = gmail_service.move_message(mock_crud_service, "email1", "Test Label", "INBOX")
        
        # Verify results
        self.assertIn("label_123", result)
        self.mock_service.users.return_value.messages.return_value.modify.assert_called_once()
    
    def test_close_method(self):
        """Test service close method."""
        # Create mock service
        gmail_service = GmailService()
        gmail_service.service = self.mock_service
        
        # Test close method (should not raise exceptions)
        gmail_service.close()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_error_handling_invalid_credentials(self, mock_exists, mock_creds, mock_build):
        """Test error handling with invalid credentials."""
        # Setup mocks to simulate error
        mock_exists.return_value = True
        mock_creds.side_effect = Exception("Invalid credentials")
        
        # Test that CustomException is raised
        with self.assertRaises(CustomException):
            GmailService()
    
    @patch('services.gmail_service.build')
    @patch('services.gmail_service.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_error_handling_api_failure(self, mock_exists, mock_creds, mock_build):
        """Test error handling when Gmail API fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.return_value = self.mock_credentials
        self.mock_credentials.valid = True
        mock_build.return_value = self.mock_service
        
        # Mock API failure
        self.mock_service.users.return_value.messages.return_value.list.side_effect = Exception("API Error")
        
        # Initialize service and test
        gmail_service = GmailService()
        
        # Test that CustomException is raised
        with self.assertRaises(CustomException):
            gmail_service.fetch_emails()


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
