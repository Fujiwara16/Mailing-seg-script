"""
Email Repository - Dedicated repository for email-related database operations.
This module handles all email-specific database queries and operations.
"""

import sqlite3
from utils.exception import CustomException


class EmailRepository:
    """Repository for email-related database operations."""
    
    def __init__(self, db_connection):
        """
        Initialize email repository with database connection.
        
        Args:
            db_connection: SQLite database connection object
        """
        self.conn = db_connection
        self.c = db_connection.c
    
    def get_emails_by_rule_conditions(self, conditions, predicate="any"):
        """
        Get emails that match rule conditions using SQL.
        
        Args:
            conditions (list): List of condition dictionaries
            predicate (str): "any" or "all" - how to combine conditions
            
        Returns:
            list: Matching email records
        """
        try:
            if not conditions:
                return []
            
            # Build SQL WHERE clause from conditions
            where_parts = []
            params = []
            
            for condition in conditions:
                sql_condition, condition_params = self._build_sql_condition(condition)
                if sql_condition:
                    where_parts.append(sql_condition)
                    params.extend(condition_params)
            
            if not where_parts:
                return []
            
            # Combine conditions based on predicate
            if predicate == "all":
                where_clause = " AND ".join(f"({part})" for part in where_parts)
            else:  # "any"
                where_clause = " OR ".join(f"({part})" for part in where_parts)
            
            # Execute query
            query = f"SELECT * FROM emails WHERE {where_clause}"
            self.c.execute(query, params)
            return self.c.fetchall()
            
        except sqlite3.Error as e:
            raise CustomException(f"Error querying emails by rule conditions: {e}")

    def _build_sql_condition(self, condition):
        """
        Build SQL condition from rule condition.
        
        Args:
            condition (dict): Condition with field, predicate, value
            
        Returns:
            tuple: (sql_condition, params)
        """
        field = condition.get("field")
        predicate = condition.get("predicate")
        value = condition.get("value", "")
        
        if not field or not predicate or not value:
            return None, []
        
        # Map fields to database columns
        field_mapping = {
            "from": "sender",
            "subject": "subject",
            "message": "snippet",
            "received": "received"
        }
        
        db_field = field_mapping.get(field)
        if not db_field:
            return None, []
        
        # Build SQL condition based on predicate
        if field == "received":
            return self._build_date_condition(db_field, predicate, value)
        else:
            return self._build_string_condition(db_field, predicate, value)

    def _build_string_condition(self, field, predicate, value):
        """Build SQL condition for string fields."""
        value_lower = value.lower()
        
        if predicate == "contains":
            return f"LOWER({field}) LIKE ?", [f"%{value_lower}%"]
        elif predicate == "does_not_contain":
            return f"LOWER({field}) NOT LIKE ?", [f"%{value_lower}%"]
        elif predicate == "equals":
            return f"LOWER({field}) = ?", [value_lower]
        elif predicate == "does_not_equal":
            return f"LOWER({field}) != ?", [value_lower]
        else:
            return None, []

    def _build_date_condition(self, field, predicate, value):
        """Build SQL condition for date fields."""
        try:
            days = int(value)
            
            if predicate == "less_than_days":
                # Email is newer than X days ago (received within the last X days)
                return f"datetime({field}) >= datetime('now', '-{days} days')", []
            elif predicate == "greater_than_days":
                # Email is older than X days ago (received more than X days ago)
                return f"datetime({field}) <= datetime('now', '-{days} days')", []
            elif predicate == "less_than_months":
                # Email is newer than X months ago (received within the last X months)
                return f"datetime({field}) >= datetime('now', '-{days * 30} days')", []
            elif predicate == "greater_than_months":
                # Email is older than X months ago (received more than X months ago)
                return f"datetime({field}) <= datetime('now', '-{days * 30} days')", []
            else:
                return None, []
        except ValueError:
            return None, []


    def batch_insert_emails(self, emails):
        """
        Batch insert multiple emails for better performance.
        
        Args:
            emails (list): List of email dictionaries to insert
        """
        try:
            if not emails:
                return []
            
            # Prepare data for batch insert
            email_data = []
            for email in emails:
                email_data.append((
                    email.get("id"),
                    email.get("sender"),
                    email.get("subject"),
                    email.get("snippet"),
                    email.get("received"),
                    email.get("labels")
                ))
            
            # Use executemany for batch insert
            self.c.executemany("""
                INSERT OR IGNORE INTO emails (id, sender, subject, snippet, received, labels)
                VALUES (?, ?, ?, ?, ?, ?)
            """, email_data)
            
            self.conn.commit()
            return emails
        except sqlite3.Error as e:
            raise CustomException(f"Error batch inserting emails: {e}")

    def mark_as_read(self, message_id):
        """Mark an email as read."""
        try:
            self.c.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (message_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error marking email as read: {e}")

    def mark_as_unread(self, message_id):
        """Mark an email as unread."""
        try:
            self.c.execute("UPDATE emails SET is_read = 0 WHERE id = ?", (message_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error marking email as unread: {e}")

    def move_message(self, message_id, labels):
        """Move an email to a different label/folder."""
        try:
            self.c.execute("UPDATE emails SET labels = ? WHERE id = ?", (labels, message_id))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error moving email to {labels}: {e}")

    def get_all_emails(self):
        """Get all emails from the database."""
        try:
            self.c.execute("SELECT * FROM emails")
            return self.c.fetchall()
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching emails: {e}")

    def get_email_count(self):
        """Get the number of emails in the database."""
        try:
            self.c.execute("SELECT COUNT(*) FROM emails")
            return self.c.fetchone()[0]
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching email count: {e}")