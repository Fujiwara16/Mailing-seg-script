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

    def insert_label(self, label):
        try:
            self.c.execute("INSERT OR IGNORE INTO labels (id, name) VALUES (?, ?)", (label["id"], label["name"]))
            self.conn.commit()
            return label
        except sqlite3.Error as e:
            raise CustomException(f"Error inserting label: {e}")

    def get_all_labels(self):
        try:
            self.c.execute("SELECT * FROM labels")
            rows = self.c.fetchall()
            # Convert to list of dictionaries
            labels = []
            for row in rows:
                if len(row) != 2:
                    raise CustomException(f"Invalid label row: {row}")
                labels.append({"id": row[0], "name": row[1]})
            return labels
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching labels: {e}")

    def insert_email(self, email):
        # Deprecated, using batch insert_emails instead
        try:
            self.c.execute("""
                INSERT OR IGNORE INTO emails (id, sender, subject, snippet, received, labels)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email.get("id"), email.get("sender"), email.get("subject"), email.get("snippet"), email.get("received"), email.get("labels")))
            self.conn.commit()
            return email
        except sqlite3.Error as e:
            raise CustomException(f"Error inserting email: {e}")

    def batch_insert_emails(self, emails):
        """
        Batch insert multiple emails for better performance.
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

    def get_all_emails(self):
        try:
            self.c.execute("SELECT * FROM emails")
            return self.c.fetchall()
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching emails: {e}")

    def mark_as_read(self, message_id):
        try:
            self.c.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (message_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error marking email as read: {e}")

    def move_message(self, message_id, labels):
        try:
            self.c.execute("UPDATE emails SET labels = ? WHERE id = ?", (labels, message_id))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error moving email to {labels}: {e}")

    def mark_as_unread(self, message_id):
        try:
            self.c.execute("UPDATE emails SET is_read = 0 WHERE id = ?", (message_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise CustomException(f"Error marking email as unread: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()