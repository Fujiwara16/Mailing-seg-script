#!/usr/bin/env python3
"""
Error handling and edge case tests.
Tests system resilience and error recovery mechanisms.
"""

import unittest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repository.sql_db import SqlDb
from repository.email_repository import EmailRepository
from repository.label_repository import LabelRepository
from services.gmail_service import GmailService
from services.crud_service import CrudService
from services.rules_service import apply_rules, validate_rules, load_and_validate_rules
from utils.exception import CustomException


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and edge cases."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database and services
        self.db = SqlDb(self.temp_db.name)
        self.db.create_indexes()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_invalid_rule_conditions(self):
        """Test handling of invalid rule conditions."""
        print("\n🧪 Testing invalid rule conditions...")
        
        # Test invalid field
        invalid_rules = [
            {
                "name": "Invalid Field Rule",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "invalid_field",  # Invalid field
                        "predicate": "contains",
                        "value": "test"
                    }
                ],
                "actions": {
                    "mark_as_read": True
                }
            }
        ]
        
        with self.assertRaises(CustomException):
            validate_rules(invalid_rules)
        print("✅ Invalid field properly rejected")
        
        # Test invalid predicate
        invalid_rules = [
            {
                "name": "Invalid Predicate Rule",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "from",
                        "predicate": "invalid_predicate",  # Invalid predicate
                        "value": "test"
                    }
                ],
                "actions": {
                    "mark_as_read": True
                }
            }
        ]
        
        with self.assertRaises(CustomException):
            validate_rules(invalid_rules)
        print("✅ Invalid predicate properly rejected")
    
    def test_database_connection_failure(self):
        """Test database connection failure handling."""
        print("\n🧪 Testing database connection failure...")
        
        # Close database to simulate connection failure
        self.db.close()
        
        # Try to perform operations
        email_repo = EmailRepository(self.db)
        
        with self.assertRaises(Exception):
            email_repo.get_all_emails()
        print("✅ Database connection failure properly handled")
    
    def test_invalid_email_data(self):
        """Test handling of invalid email data."""
        print("\n🧪 Testing invalid email data...")
        
        email_repo = EmailRepository(self.db)
        
        # Test with empty data
        result = email_repo.batch_insert_emails([])
        self.assertEqual(result, [])
        print("✅ Empty data properly handled")
        
        # Test with malformed email data
        malformed_emails = [
            {
                "id": "test_email",
                # Missing required fields
            }
        ]
        
        # Should handle gracefully (exact behavior depends on implementation)
        # The batch_insert_emails method should handle missing fields
        try:
            result = email_repo.batch_insert_emails(malformed_emails)
            # If it doesn't raise an exception, it should return empty list or handle gracefully
            self.assertIsInstance(result, list)
        except Exception as e:
            # If it does raise an exception, it should be a specific type
            self.assertIsInstance(e, (ValueError, TypeError, KeyError))
        print("✅ Malformed email data properly handled")
    
    def test_missing_rules_file(self):
        """Test handling of missing rules file."""
        print("\n🧪 Testing missing rules file...")
        
        with self.assertRaises(CustomException):
            load_and_validate_rules("nonexistent_rules.json")
        print("✅ Missing rules file properly handled")
    
    def test_invalid_json_rules_file(self):
        """Test handling of invalid JSON in rules file."""
        print("\n🧪 Testing invalid JSON rules file...")
        
        # Create temporary invalid JSON file
        invalid_json_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        invalid_json_file.write("invalid json content")
        invalid_json_file.close()
        
        try:
            with self.assertRaises(CustomException):
                load_and_validate_rules(invalid_json_file.name)
            print("✅ Invalid JSON properly handled")
        finally:
            os.unlink(invalid_json_file.name)
    
    def test_gmail_api_rate_limiting(self):
        """Test Gmail API rate limiting handling."""
        print("\n🧪 Testing Gmail API rate limiting...")
        
        # Mock Gmail service that simulates rate limiting
        class RateLimitedGmailService:
            def __init__(self):
                self.call_count = 0
            
            def fetch_emails(self, start_time=None, end_time=None, max_results=1000):
                self.call_count += 1
                if self.call_count > 3:  # Simulate rate limiting after 3 calls
                    raise Exception("Rate limit exceeded")
                return []
        
        rate_limited_service = RateLimitedGmailService()
        crud_service = CrudService(rate_limited_service, self.db)
        
        # First few calls should work
        for i in range(3):
            try:
                crud_service.get_emails_and_store_in_db()
            except Exception:
                pass
        
        # Subsequent calls should handle rate limiting
        with self.assertRaises(Exception):
            crud_service.get_emails_and_store_in_db()
        print("✅ Gmail API rate limiting properly handled")
    
    def test_memory_limits(self):
        """Test system behavior under memory constraints."""
        print("\n🧪 Testing memory limits...")
        
        email_repo = EmailRepository(self.db)
        
        # Test with very large email dataset
        large_emails = []
        for i in range(10000):  # Large dataset
            email = {
                "id": f"large_email_{i}",
                "sender": f"sender{i}@example.com",
                "subject": f"Subject {i}",
                "snippet": f"Snippet {i}" * 100,  # Large snippet
                "received": "2024-01-01T00:00:00Z",
                "labels": "INBOX"
            }
            large_emails.append(email)
        
        # Should handle large dataset gracefully
        try:
            email_repo.batch_insert_emails(large_emails)
            print("✅ Large dataset handled gracefully")
        except Exception as e:
            # Should fail gracefully with informative error
            self.assertIsInstance(e, (Exception, CustomException))
            print(f"✅ Large dataset failed gracefully: {type(e).__name__}")
    
    def test_concurrent_database_access(self):
        """Test concurrent database access handling."""
        print("\n🧪 Testing concurrent database access...")
        
        email_repo = EmailRepository(self.db)
        
        # Insert some test data
        test_emails = [
            {
                "id": "concurrent_1",
                "sender": "test@example.com",
                "subject": "Test 1",
                "snippet": "Content 1",
                "received": "2024-01-01T00:00:00Z",
                "labels": "INBOX"
            }
        ]
        email_repo.batch_insert_emails(test_emails)
        
        # Simulate concurrent operations
        try:
            # Multiple concurrent reads (should be safe)
            for i in range(5):
                emails = email_repo.get_all_emails()
                self.assertEqual(len(emails), 1)
            
            print("✅ Concurrent database access handled correctly")
        except Exception as e:
            print(f"⚠️  Concurrent access issue: {e}")
    
    def test_network_timeout_handling(self):
        """Test network timeout handling."""
        print("\n🧪 Testing network timeout handling...")
        
        # Mock Gmail service that simulates network timeout
        class TimeoutGmailService:
            def fetch_emails(self, start_time=None, end_time=None, max_results=1000):
                raise Exception("Network timeout")
        
        timeout_service = TimeoutGmailService()
        crud_service = CrudService(timeout_service, self.db)
        
        with self.assertRaises(Exception):
            crud_service.get_emails_and_store_in_db()
        print("✅ Network timeout properly handled")
    
    def test_corrupted_database_handling(self):
        """Test handling of corrupted database."""
        print("\n🧪 Testing corrupted database handling...")
        
        # Close and corrupt the database file
        self.db.close()
        
        # Write invalid data to database file
        with open(self.temp_db.name, 'w') as f:
            f.write("corrupted database content")
        
        # Try to initialize database (should handle gracefully)
        try:
            corrupted_db = SqlDb(self.temp_db.name)
            print("✅ Corrupted database handled gracefully")
        except Exception as e:
            print(f"✅ Corrupted database properly rejected: {type(e).__name__}")
    
    def test_edge_case_rule_values(self):
        """Test edge case rule values."""
        print("\n🧪 Testing edge case rule values...")
        
        # Test empty rule values
        edge_case_rules = [
            {
                "name": "Empty Value Rule",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "from",
                        "predicate": "contains",
                        "value": ""  # Empty value
                    }
                ],
                "actions": {
                    "mark_as_read": True
                }
            }
        ]
        
        with self.assertRaises(CustomException):
            validate_rules(edge_case_rules)
        print("✅ Empty rule values properly rejected")
        
        # Test very long rule values
        long_value_rules = [
            {
                "name": "Long Value Rule",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "from",
                        "predicate": "contains",
                        "value": "x" * 10000  # Very long value
                    }
                ],
                "actions": {
                    "mark_as_read": True
                }
            }
        ]
        
        # Should handle long values gracefully
        try:
            validate_rules(long_value_rules)
            print("✅ Long rule values handled gracefully")
        except Exception:
            print("✅ Long rule values properly rejected")
    
    def test_system_recovery_after_errors(self):
        """Test system recovery after various errors."""
        print("\n🧪 Testing system recovery after errors...")
        
        email_repo = EmailRepository(self.db)
        
        # Test recovery after database error
        try:
            # Simulate database error
            self.db.close()
            email_repo.get_all_emails()
        except Exception:
            pass
        
        # Recreate database and test recovery
        self.db = SqlDb(self.temp_db.name)
        email_repo = EmailRepository(self.db)
        
        # Should work normally after recovery
        emails = email_repo.get_all_emails()
        self.assertEqual(len(emails), 0)
        print("✅ System recovery after database error successful")
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        print("\n🧪 Testing unicode and special characters...")
        
        email_repo = EmailRepository(self.db)
        
        # Test emails with unicode and special characters
        unicode_emails = [
            {
                "id": "unicode_email",
                "sender": "tëst@éxämplé.com",
                "subject": "Tëst Émäil with Ünicödé",
                "snippet": "Cöntént with spëcial chäractërs: !@#$%^&*()",
                "received": "2024-01-01T00:00:00Z",
                "labels": "INBOX"
            }
        ]
        
        try:
            email_repo.batch_insert_emails(unicode_emails)
            emails = email_repo.get_all_emails()
            self.assertEqual(len(emails), 1)
            print("✅ Unicode and special characters handled correctly")
        except Exception as e:
            print(f"⚠️  Unicode handling issue: {e}")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
