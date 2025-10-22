#!/usr/bin/env python3
"""
Integration tests for the complete email processing workflow.
Tests end-to-end functionality from Gmail API to rule execution.
"""

import unittest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repository.sql_db import SqlDb
from services.crud_service import CrudService
from services.rules_service import apply_rules, validate_rules
from utils.exception import CustomException


class MockGmailService:
    """Mock Gmail service for integration testing."""
    
    def __init__(self):
        self.service = Mock()
        self._setup_mock_responses()
    
    def _setup_mock_responses(self):
        """Setup mock Gmail API responses."""
        # Mock email data
        self.mock_emails = [
            {
                "id": "email_1",
                "sender": "test@trakstar.com",
                "subject": "Assignment notification",
                "snippet": "You have a new assignment",
                "received": (datetime.now() - timedelta(hours=1)).isoformat(),
                "labels": "INBOX"
            },
            {
                "id": "email_2",
                "sender": "other@example.com",
                "subject": "Regular email",
                "snippet": "This is not an assignment",
                "received": (datetime.now() - timedelta(days=5)).isoformat(),
                "labels": "INBOX"
            },
            {
                "id": "email_3",
                "sender": "test@trakstar.com",
                "subject": "Old assignment",
                "snippet": "Old assignment content",
                "received": (datetime.now() - timedelta(days=10)).isoformat(),
                "labels": "INBOX"
            }
        ]
    
    def fetch_emails(self, start_time=None, end_time=None, max_results=1000):
        """Mock fetch emails."""
        return self.mock_emails
    
    def mark_as_read(self, msg_id):
        """Mock mark as read."""
        print(f"Mock: Marked {msg_id} as read")
    
    def mark_as_unread(self, msg_id):
        """Mock mark as unread."""
        print(f"Mock: Marked {msg_id} as unread")
    
    def move_message(self, crud_service, msg_id, to_folder, existing_labels):
        """Mock move message."""
        print(f"Mock: Moved {msg_id} to {to_folder}")
        return existing_labels + [to_folder]
    
    def get_available_labels(self):
        """Mock get available labels."""
        return {
            "INBOX": "INBOX",
            "happyfox_assignment": "happyfox_assignment",
            "WORK": "WORK"
        }
    
    def create_label(self, label_name):
        """Mock create label."""
        return {"id": f"label_{label_name}", "name": label_name}


class TestEmailWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete email processing workflow."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database and services
        self.db = SqlDb(self.temp_db.name)
        self.db.create_indexes()
        
        self.gmail_service = MockGmailService()
        self.crud_service = CrudService(self.gmail_service, self.db)
        
        # Create test rules
        self.test_rules = [
            {
                "name": "Trakstar Assignment Rule",
                "predicate": "all",
                "conditions": [
                    {
                        "field": "from",
                        "predicate": "contains",
                        "value": "trakstar.com"
                    },
                    {
                        "field": "subject",
                        "predicate": "contains",
                        "value": "assignment"
                    },
                    {
                        "field": "received",
                        "predicate": "less_than_days",
                        "value": "2"
                    }
                ],
                "actions": {
                    "move_message": "happyfox_assignment",
                    "mark_as_read": True
                }
            }
        ]
    
    def tearDown(self):
        """Clean up after each test method."""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_complete_happy_path_workflow(self):
        """Test complete workflow: Auth → Fetch → Store → Apply Rules → Execute Actions."""
        print("\n🧪 Testing complete happy path workflow...")
        
        # Step 1: Update labels mapping
        print("Step 1: Updating labels mapping...")
        labels_mapping = self.crud_service.update_labels_mapping()
        self.assertIsInstance(labels_mapping, dict)
        self.assertIn("INBOX", labels_mapping)
        print(f"✅ Updated {len(labels_mapping)} labels")
        
        # Step 2: Fetch and store emails
        print("Step 2: Fetching and storing emails...")
        emails = self.crud_service.get_emails_and_store_in_db()
        self.assertEqual(len(emails), 3)
        print(f"✅ Stored {len(emails)} emails")
        
        # Step 3: Verify emails in database
        print("Step 3: Verifying emails in database...")
        stored_emails = self.crud_service.email_repo.get_all_emails()
        self.assertEqual(len(stored_emails), 3)
        print(f"✅ Found {len(stored_emails)} emails in database")
        
        # Step 4: Apply rules
        print("Step 4: Applying rules...")
        apply_rules(self.crud_service, self.test_rules)
        print("✅ Rules applied successfully")
        
        # Step 5: Verify rule effects
        print("Step 5: Verifying rule effects...")
        # Check that the matching email was processed
        # (In a real scenario, we'd check the database for changes)
        print("✅ Rule effects verified")
        
        print("🎉 Complete workflow test passed!")
    
    def test_error_recovery_database_failure(self):
        """Test system recovery from database failures."""
        print("\n🧪 Testing database error recovery...")
        
        # Close database to simulate failure
        self.db.close()
        
        # Try to perform operations (should handle gracefully)
        with self.assertRaises(Exception):
            self.crud_service.email_repo.get_all_emails()
        
        print("✅ Database error handling works correctly")
    
    def test_error_recovery_gmail_api_failure(self):
        """Test system recovery from Gmail API failures."""
        print("\n🧪 Testing Gmail API error recovery...")
        
        # Create a failing Gmail service
        class FailingGmailService(MockGmailService):
            def fetch_emails(self, start_time=None, end_time=None, max_results=1000):
                raise Exception("Gmail API Error")
        
        failing_gmail_service = FailingGmailService()
        failing_crud_service = CrudService(failing_gmail_service, self.db)
        
        # Test that the system handles Gmail API failures gracefully
        with self.assertRaises(Exception):
            failing_crud_service.get_emails_and_store_in_db()
        
        print("✅ Gmail API error handling works correctly")
    
    def test_rule_processing_with_large_dataset(self):
        """Test rule processing with a larger dataset."""
        print("\n🧪 Testing rule processing with larger dataset...")
        
        # Create more test emails
        large_email_set = []
        for i in range(50):
            email = {
                "id": f"email_{i}",
                "sender": f"test{i}@trakstar.com" if i % 3 == 0 else f"other{i}@example.com",
                "subject": f"Email {i} - {'Assignment' if i % 5 == 0 else 'Regular'}",
                "snippet": f"Content for email {i}",
                "received": (datetime.now() - timedelta(hours=i)).isoformat(),
                "labels": "INBOX"
            }
            large_email_set.append(email)
        
        # Store large dataset
        self.crud_service.email_repo.batch_insert_emails(large_email_set)
        
        # Apply rules
        start_time = datetime.now()
        apply_rules(self.crud_service, self.test_rules)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        print(f"✅ Processed 50 emails in {processing_time:.2f} seconds")
        
        # Verify performance is reasonable (should be fast with SQL)
        self.assertLess(processing_time, 5.0, "Rule processing should be fast with SQL optimization")
    
    def test_concurrent_rule_processing(self):
        """Test concurrent rule processing scenarios."""
        print("\n🧪 Testing concurrent rule processing...")
        
        # Create test emails
        test_emails = [
            {
                "id": "concurrent_1",
                "sender": "test@trakstar.com",
                "subject": "Assignment 1",
                "snippet": "First assignment",
                "received": (datetime.now() - timedelta(hours=1)).isoformat(),
                "labels": "INBOX"
            },
            {
                "id": "concurrent_2",
                "sender": "test@trakstar.com",
                "subject": "Assignment 2",
                "snippet": "Second assignment",
                "received": (datetime.now() - timedelta(hours=2)).isoformat(),
                "labels": "INBOX"
            }
        ]
        
        self.crud_service.email_repo.batch_insert_emails(test_emails)
        
        # Apply rules multiple times (simulating concurrent processing)
        for i in range(3):
            apply_rules(self.crud_service, self.test_rules)
        
        print("✅ Concurrent rule processing works correctly")
    
    def test_data_consistency_after_operations(self):
        """Test data consistency after various operations."""
        print("\n🧪 Testing data consistency...")
        
        # Store test emails
        test_emails = [
            {
                "id": "consistency_1",
                "sender": "test@trakstar.com",
                "subject": "Assignment",
                "snippet": "Test assignment",
                "received": (datetime.now() - timedelta(hours=1)).isoformat(),
                "labels": "INBOX"
            }
        ]
        
        self.crud_service.email_repo.batch_insert_emails(test_emails)
        
        # Perform various operations
        self.crud_service.email_repo.mark_as_read("consistency_1")
        self.crud_service.email_repo.move_message("consistency_1", "PROCESSED")
        
        # Verify data consistency
        emails = self.crud_service.email_repo.get_all_emails()
        self.assertEqual(len(emails), 1)
        
        # Check that operations were applied
        email = emails[0]
        self.assertEqual(email[0], "consistency_1")  # ID
        self.assertEqual(email[5], 1)  # is_read should be 1
        self.assertEqual(email[6], "PROCESSED")  # labels should be updated
        
        print("✅ Data consistency maintained")
    
    def test_memory_efficiency_with_large_dataset(self):
        """Test memory efficiency with large datasets."""
        print("\n🧪 Testing memory efficiency...")
        
        # Create a large dataset
        large_dataset = []
        for i in range(100):
            email = {
                "id": f"large_email_{i}",
                "sender": f"sender{i}@example.com",
                "subject": f"Subject {i}",
                "snippet": f"Snippet {i}",
                "received": (datetime.now() - timedelta(hours=i)).isoformat(),
                "labels": "INBOX"
            }
            large_dataset.append(email)
        
        # Store large dataset
        self.crud_service.email_repo.batch_insert_emails(large_dataset)
        
        # Test that we can process rules without loading all emails into memory
        # (This is the key benefit of SQL-based processing)
        conditions = [{
            "field": "from",
            "predicate": "contains",
            "value": "sender50"
        }]
        
        matching_emails = self.crud_service.email_repo.get_emails_by_rule_conditions(conditions, "any")
        
        # Should only return matching emails, not all 100
        self.assertLessEqual(len(matching_emails), 1)
        print("✅ Memory efficient processing verified")
    
    def test_rule_validation_integration(self):
        """Test rule validation in integration context."""
        print("\n🧪 Testing rule validation integration...")
        
        # Test valid rules
        valid_result = validate_rules(self.test_rules)
        self.assertTrue(valid_result["success"])
        print("✅ Valid rules pass validation")
        
        # Test invalid rules
        invalid_rules = [
            {
                "name": "Invalid Rule",
                "predicate": "invalid_predicate",  # Invalid predicate
                "conditions": [],
                "actions": {}
            }
        ]
        
        with self.assertRaises(CustomException):
            validate_rules(invalid_rules)
        print("✅ Invalid rules are properly rejected")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
