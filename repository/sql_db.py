import sqlite3
import logging
from utils.exception import CustomException
class SqlDb:
    def __init__(self, db_path):
        try:
            self.conn = sqlite3.connect(db_path)
            self.c = self.conn.cursor()
            self.c.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    sender TEXT,
                    subject TEXT,
                    snippet TEXT,
                    received TEXT,
                    is_read INTEGER DEFAULT 0,
                    labels TEXT DEFAULT 'INBOX'
                )
            """)
            self.c.execute("""
                CREATE TABLE IF NOT EXISTS labels (
                    id TEXT PRIMARY KEY,
                    name TEXT
                );
            """)
            # fully empty the labels table
            self.c.execute("DELETE FROM labels")
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Database initialization error: {e}")

    def commit(self):
        """Commit database transactions."""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """Rollback database transactions."""
        if self.conn:
            self.conn.rollback()

    def create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Create indexes on frequently queried fields for rule processing
            self.c.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)")
            self.c.execute("CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject)")
            self.c.execute("CREATE INDEX IF NOT EXISTS idx_emails_received ON emails(received)")
            
            self.conn.commit()
            print("✅ Database indexes created successfully")
        except sqlite3.Error as e:
            raise CustomException(f"Error creating indexes: {e}")

    def __del__(self):
        self.close()


    def close(self):
        if self.conn:
            self.conn.close()
