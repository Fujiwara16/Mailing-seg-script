#!/usr/bin/env python3
"""
Unit tests for SQL-based rule processing.
Tests the new SQL approach with existing rules using unittest framework.
"""

import unittest
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repository.sql_db import SqlDb
from services.rules_service import apply_rules, validate_rules
from services.crud_service import CrudService


class MockGmailService:
    """Mock Gmail service for testing."""
    
    def mark_as_read(self, msg_id):
        """Mock mark as read."""
        pass
    
    def mark_as_unread(self, msg_id):
        """Mock mark as unread."""
        pass
    
    def move_message(self, crud_service, msg_id, to_folder, existing_labels):
        """Mock move message."""
        return existing_labels + to_folder
    
    def get_available_labels(self):
        """Mock get available labels."""
        return {"INBOX": "INBOX", "happyfox_assignment": "happyfox_assignment"}


class TestSQLRules(unittest.TestCase):
    """Test cases for SQL-based rule processing."""
    
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
        
        # Create test emails
        self._create_test_emails()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def _create_test_emails(self):
        """Create test emails for rule testing."""
        now = datetime.now()
        test_emails = [
            {
                "id": "test_email_1",
                "sender": "test@trakstar.com",
                "subject": "Assignment notification",
                "snippet": "You have a new assignment",
                "received": (now - timedelta(hours=1)).isoformat(),  # 1 hour ago
                "labels": "INBOX"
            },
            {
                "id": "test_email_2",
                "sender": "other@example.com",
                "subject": "Regular email",
                "snippet": "This is not an assignment",
                "received": (now - timedelta(days=5)).isoformat(),  # 5 days ago
                "labels": "INBOX"
            },
            {
                "id": "test_email_3",
                "sender": "test@trakstar.com",
                "subject": "Old assignment",
                "snippet": "Old assignment content",
                "received": (now - timedelta(days=10)).isoformat(),  # 10 days ago
                "labels": "INBOX"
            }
        ]
        
        self.crud_service.email_repo.batch_insert_emails(test_emails)
    
    def test_rule_validation(self):
        """Test rule validation functionality."""
        with open("rules.json", "r") as f:
            rules_data = json.load(f)
        
        # Test validation
        result = validate_rules(rules_data)
        self.assertTrue(result["success"], "Rules should be valid")
        self.assertEqual(len(rules_data), 1, "Should have 1 rule group")
    
    def test_sql_rule_processing(self):
        """Test SQL-based rule processing."""
        with open("rules.json", "r") as f:
            rules_data = json.load(f)
        try:
            apply_rules(self.crud_service, rules_data)
        except Exception as e:
            self.fail(f"Rule processing failed: {e}")
    
    def test_date_condition_less_than_days(self):
        """Test date condition with less_than_days predicate."""
        conditions = [{
            "field": "received",
            "predicate": "less_than_days",
            "value": "2"
        }]
        
        # Get emails matching the condition
        matching_emails = self.crud_service.email_repo.get_emails_by_rule_conditions(conditions, "any")
        
        # Should find emails from the last 2 days
        self.assertGreater(len(matching_emails), 0, "Should find emails from last 2 days")
        
        # Verify the emails are actually recent
        for email in matching_emails:
            received_date = datetime.fromisoformat(email[4])
            days_ago = (datetime.now() - received_date).days
            self.assertLessEqual(days_ago, 2, f"Email should be from last 2 days, but was {days_ago} days ago")
    
    def test_string_condition_contains(self):
        """Test string condition with contains predicate."""
        conditions = [{
            "field": "from",
            "predicate": "contains",
            "value": "trakstar.com"
        }]
        
        # Get emails matching the condition
        matching_emails = self.crud_service.email_repo.get_emails_by_rule_conditions(conditions, "any")
        
        # Should find emails from trakstar.com
        self.assertGreater(len(matching_emails), 0, "Should find emails from trakstar.com")
        
        # Verify all matching emails are from trakstar.com
        for email in matching_emails:
            self.assertIn("trakstar.com", email[1].lower(), "Email should be from trakstar.com")
    
    def test_combined_conditions_all_predicate(self):
        """Test combined conditions with 'all' predicate."""
        conditions = [
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
        ]
        
        # Get emails matching ALL conditions
        matching_emails = self.crud_service.email_repo.get_emails_by_rule_conditions(conditions, "all")
        
        # Should find emails that match ALL conditions
        for email in matching_emails:
            # Check sender
            self.assertIn("trakstar.com", email[1].lower(), "Email should be from trakstar.com")
            # Check subject
            self.assertIn("assignment", email[2].lower(), "Email subject should contain 'assignment'")
            # Check date
            received_date = datetime.fromisoformat(email[4])
            days_ago = (datetime.now() - received_date).days
            self.assertLessEqual(days_ago, 2, "Email should be from last 2 days")
    
    def test_combined_conditions_any_predicate(self):
        """Test combined conditions with 'any' predicate."""
        conditions = [
            {
                "field": "from",
                "predicate": "contains",
                "value": "trakstar.com"
            },
            {
                "field": "subject",
                "predicate": "contains",
                "value": "nonexistent"
            }
        ]
        
        # Get emails matching ANY condition
        matching_emails = self.crud_service.email_repo.get_emails_by_rule_conditions(conditions, "any")
        
        # Should find emails that match at least one condition
        self.assertGreater(len(matching_emails), 0, "Should find emails matching any condition")
        
        # All matching emails should be from trakstar.com (since that's the only matching condition)
        for email in matching_emails:
            self.assertIn("trakstar.com", email[1].lower(), "Email should be from trakstar.com")
    
    def test_email_repository_methods(self):
        """Test EmailRepository methods."""
        # Test get all emails
        all_emails = self.crud_service.email_repo.get_all_emails()
        self.assertEqual(len(all_emails), 3, "Should have 3 test emails")
        
        # Test mark as read
        self.crud_service.email_repo.mark_as_read("test_email_1")
        
        # Test move message
        self.crud_service.email_repo.move_message("test_email_1", "TEST_LABEL")
    
    def test_label_repository_methods(self):
        """Test LabelRepository methods."""
        # Test insert label
        test_label = {"id": "test_label", "name": "Test Label"}
        self.crud_service.label_repo.insert_label(test_label)
        
        # Test get all labels
        labels = self.crud_service.label_repo.get_all_labels()
        self.assertGreater(len(labels), 0, "Should have labels")
        
        # Test get label by name
        found_label = self.crud_service.label_repo.get_label_by_name("Test Label")
        self.assertIsNotNone(found_label, "Should find the test label")
        self.assertEqual(found_label["name"], "Test Label")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
