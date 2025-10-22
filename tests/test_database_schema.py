#!/usr/bin/env python3
"""
Database schema and migration tests.
Tests database structure, indexes, and data integrity.
"""

import unittest
import os
import sys
import tempfile
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repository.sql_db import SqlDb
from repository.email_repository import EmailRepository
from repository.label_repository import LabelRepository
from utils.exception import CustomException


class TestDatabaseSchema(unittest.TestCase):
    """Test cases for database schema and structure."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database
        self.db = SqlDb(self.temp_db.name)
    
    def tearDown(self):
        """Clean up after each test method."""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_table_creation(self):
        """Test that tables are created correctly."""
        print("\n🧪 Testing table creation...")
        
        # Check that emails table exists
        cursor = self.db.c
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        emails_table = cursor.fetchone()
        self.assertIsNotNone(emails_table, "emails table should exist")
        print("✅ emails table created")
        
        # Check that labels table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='labels'")
        labels_table = cursor.fetchone()
        self.assertIsNotNone(labels_table, "labels table should exist")
        print("✅ labels table created")
    
    def test_emails_table_schema(self):
        """Test emails table schema."""
        print("\n🧪 Testing emails table schema...")
        
        cursor = self.db.c
        cursor.execute("PRAGMA table_info(emails)")
        columns = cursor.fetchall()
        
        # Expected columns: id, sender, subject, snippet, received, is_read, labels
        expected_columns = ['id', 'sender', 'subject', 'snippet', 'received', 'is_read', 'labels']
        actual_columns = [col[1] for col in columns]
        for expected_col in expected_columns:
            self.assertIn(expected_col, actual_columns, f"Column {expected_col} should exist")
        
        print(f"✅ emails table has correct schema: {actual_columns}")
    
    def test_labels_table_schema(self):
        """Test labels table schema."""
        print("\n🧪 Testing labels table schema...")
        
        cursor = self.db.c
        cursor.execute("PRAGMA table_info(labels)")
        columns = cursor.fetchall()
        
        # Expected columns: id, name
        expected_columns = ['id', 'name']
        actual_columns = [col[1] for col in columns]
        
        for expected_col in expected_columns:
            self.assertIn(expected_col, actual_columns, f"Column {expected_col} should exist")
        
        print(f"✅ labels table has correct schema: {actual_columns}")
    
    def test_primary_keys(self):
        """Test primary key constraints."""
        print("\n🧪 Testing primary key constraints...")
        
        cursor = self.db.c
        
        # Check emails table primary key
        cursor.execute("PRAGMA table_info(emails)")
        emails_columns = cursor.fetchall()
        id_column = next((col for col in emails_columns if col[1] == 'id'), None)
        self.assertIsNotNone(id_column, "id column should exist")
        self.assertEqual(id_column[5], 1, "id column should be primary key")
        
        # Check labels table primary key
        cursor.execute("PRAGMA table_info(labels)")
        labels_columns = cursor.fetchall()
        id_column = next((col for col in labels_columns if col[1] == 'id'), None)
        self.assertIsNotNone(id_column, "id column should exist")
        self.assertEqual(id_column[5], 1, "id column should be primary key")
        
        print("✅ Primary key constraints verified")
    
    def test_index_creation(self):
        """Test that indexes are created correctly."""
        print("\n🧪 Testing index creation...")
        
        # Create indexes
        self.db.create_indexes()
        
        cursor = self.db.c
        
        # Check that indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_emails_sender',
            'idx_emails_subject',
            'idx_emails_received'
        ]
        
        for expected_index in expected_indexes:
            self.assertIn(expected_index, indexes, f"Index {expected_index} should exist")
        
        print(f"✅ All indexes created: {len(indexes)} total")
    
    def test_data_integrity_constraints(self):
        """Test data integrity constraints."""
        print("\n🧪 Testing data integrity constraints...")
        
        cursor = self.db.c
        
        # Test that we can't insert duplicate email IDs
        cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received, labels) VALUES (?, ?, ?, ?, ?, ?)",
                      ("test_id", "test@example.com", "Test", "Content", "2024-01-01T00:00:00Z", "INBOX"))
        
        # Try to insert duplicate ID (should fail)
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received, labels) VALUES (?, ?, ?, ?, ?, ?)",
                          ("test_id", "test2@example.com", "Test2", "Content2", "2024-01-01T00:00:00Z", "INBOX"))
        
        print("✅ Primary key constraint enforced")
        
        # Test that we can't insert duplicate label IDs
        cursor.execute("INSERT INTO labels (id, name) VALUES (?, ?)", ("label_id", "Test Label"))
        
        # Try to insert duplicate label ID (should fail)
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO labels (id, name) VALUES (?, ?)", ("label_id", "Test Label 2"))
        
        print("✅ Label primary key constraint enforced")
    
    def test_default_values(self):
        """Test default values for columns."""
        print("\n🧪 Testing default values...")
        
        cursor = self.db.c
        
        # Test emails table defaults
        cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received) VALUES (?, ?, ?, ?, ?)",
                      ("default_test", "test@example.com", "Test", "Content", "2024-01-01T00:00:00Z"))
        
        cursor.execute("SELECT is_read, labels FROM emails WHERE id = ?", ("default_test",))
        row = cursor.fetchone()
        
        self.assertEqual(row[0], 0, "is_read should default to 0")
        self.assertEqual(row[1], "INBOX", "labels should default to 'INBOX'")
        
        print("✅ Default values work correctly")
    
    def test_foreign_key_constraints(self):
        """Test foreign key constraints (if any)."""
        print("\n🧪 Testing foreign key constraints...")
        
        # Note: SQLite doesn't enforce foreign keys by default
        # This test verifies the schema doesn't have unexpected foreign key issues
        
        cursor = self.db.c
        
        # Test that we can insert data without foreign key issues
        cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received, labels) VALUES (?, ?, ?, ?, ?, ?)",
                      ("fk_test", "test@example.com", "Test", "Content", "2024-01-01T00:00:00Z", "INBOX"))
        
        cursor.execute("INSERT INTO labels (id, name) VALUES (?, ?)", ("fk_label", "Test Label"))
        
        print("✅ No foreign key constraint issues")
    
    def test_database_migration_compatibility(self):
        """Test database migration compatibility."""
        print("\n🧪 Testing database migration compatibility...")
        
        # Test that we can create a new database with the same schema
        temp_db2 = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db2.close()
        
        try:
            db2 = SqlDb(temp_db2.name)
            
            # Verify both databases have the same schema
            cursor1 = self.db.c
            cursor2 = db2.c
            
            # Compare table structures
            cursor1.execute("SELECT sql FROM sqlite_master WHERE type='table'")
            tables1 = [row[0] for row in cursor1.fetchall()]
            
            cursor2.execute("SELECT sql FROM sqlite_master WHERE type='table'")
            tables2 = [row[0] for row in cursor2.fetchall()]
            
            self.assertEqual(len(tables1), len(tables2), "Both databases should have same number of tables")
            
            print("✅ Database migration compatibility verified")
            
        finally:
            db2.close()
            os.unlink(temp_db2.name)
    
    def test_database_performance_schema(self):
        """Test database performance with schema operations."""
        print("\n🧪 Testing database performance with schema operations...")
        
        import time
        
        # Test index creation performance
        start_time = time.time()
        self.db.create_indexes()
        index_creation_time = time.time() - start_time
        
        self.assertLess(index_creation_time, 5.0, "Index creation should be fast")
        print(f"✅ Index creation completed in {index_creation_time:.3f} seconds")
        
        # Test table creation performance
        start_time = time.time()
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            new_db = SqlDb(temp_db.name)
            table_creation_time = time.time() - start_time
            
            self.assertLess(table_creation_time, 2.0, "Table creation should be fast")
            print(f"✅ Table creation completed in {table_creation_time:.3f} seconds")
            
        finally:
            new_db.close()
            os.unlink(temp_db.name)
    
    def test_data_types_and_constraints(self):
        """Test data types and constraints."""
        print("\n🧪 Testing data types and constraints...")
        
        cursor = self.db.c
        
        # Test various data types
        test_data = [
            ("string_id", "test@example.com", "Test Subject", "Test content", "2024-01-01T00:00:00Z", 1, "INBOX"),
            ("numeric_id", "test2@example.com", "Test Subject 2", "Test content 2", "2024-01-02T00:00:00Z", 0, "WORK"),
            ("unicode_id", "tëst@éxämplé.com", "Tëst Sübjëct", "Tëst cöntënt", "2024-01-03T00:00:00Z", 1, "PËRSÖNAL")
        ]
        
        for data in test_data:
            cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received, is_read, labels) VALUES (?, ?, ?, ?, ?, ?, ?)", data)
        
        # Verify data was stored correctly
        cursor.execute("SELECT COUNT(*) FROM emails")
        count = cursor.fetchone()[0]
        self.assertEqual(count, len(test_data), "All test data should be stored")
        
        print("✅ Data types and constraints work correctly")
    
    def test_database_cleanup(self):
        """Test database cleanup operations."""
        print("\n🧪 Testing database cleanup...")
        
        cursor = self.db.c
        
        # Insert test data
        cursor.execute("INSERT INTO emails (id, sender, subject, snippet, received, labels) VALUES (?, ?, ?, ?, ?, ?)",
                      ("cleanup_test", "test@example.com", "Test", "Content", "2024-01-01T00:00:00Z", "INBOX"))
        
        cursor.execute("INSERT INTO labels (id, name) VALUES (?, ?)", ("cleanup_label", "Test Label"))
        
        # Verify data exists
        cursor.execute("SELECT COUNT(*) FROM emails")
        email_count = cursor.fetchone()[0]
        self.assertEqual(email_count, 1)
        
        cursor.execute("SELECT COUNT(*) FROM labels")
        label_count = cursor.fetchone()[0]
        self.assertEqual(label_count, 1)
        
        # Test cleanup operations
        cursor.execute("DELETE FROM emails WHERE id = ?", ("cleanup_test",))
        cursor.execute("DELETE FROM labels WHERE id = ?", ("cleanup_label",))
        
        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM emails")
        email_count = cursor.fetchone()[0]
        self.assertEqual(email_count, 0)
        
        cursor.execute("SELECT COUNT(*) FROM labels")
        label_count = cursor.fetchone()[0]
        self.assertEqual(label_count, 0)
        
        print("✅ Database cleanup operations work correctly")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
