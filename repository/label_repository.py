"""
Label Repository - Dedicated repository for label-related database operations.
This module handles all label-specific database queries and operations.
"""

import sqlite3
from utils.exception import CustomException


class LabelRepository:
    """Repository for label-related database operations."""
    
    def __init__(self, db_connection):
        """
        Initialize label repository with database connection.
        
        Args:
            db_connection: SQLite database connection object
        """
        self.conn = db_connection.conn
        self.c = db_connection.c
    
    def insert_label(self, label):
        """
        Insert a new label into the database.
        
        Args:
            label (dict): Label dictionary with 'id' and 'name' keys
            
        Returns:
            dict: The inserted label
        """
        try:
            self.c.execute("INSERT OR IGNORE INTO labels (id, name) VALUES (?, ?)", (label["id"], label["name"]))
            self.conn.commit()
            return label
        except sqlite3.Error as e:
            raise CustomException(f"Error inserting label: {e}")

    def get_all_labels(self):
        """
        Get all labels from the database.
        
        Returns:
            list: List of label dictionaries
        """
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

    def get_label_by_id(self, label_id):
        """
        Get a specific label by ID.
        
        Args:
            label_id (str): Label ID to search for
            
        Returns:
            dict: Label dictionary or None if not found
        """
        try:
            self.c.execute("SELECT * FROM labels WHERE id = ?", (label_id,))
            row = self.c.fetchone()
            if row:
                return {"id": row[0], "name": row[1]}
            return None
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching label by ID: {e}")

    def get_label_by_name(self, label_name):
        """
        Get a specific label by name.
        
        Args:
            label_name (str): Label name to search for
            
        Returns:
            dict: Label dictionary or None if not found
        """
        try:
            self.c.execute("SELECT * FROM labels WHERE name = ?", (label_name,))
            row = self.c.fetchone()
            if row:
                return {"id": row[0], "name": row[1]}
            return None
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching label by name: {e}")

    def update_label(self, label_id, new_name):
        """
        Update a label's name.
        
        Args:
            label_id (str): Label ID to update
            new_name (str): New name for the label
            
        Returns:
            bool: True if update was successful
        """
        try:
            self.c.execute("UPDATE labels SET name = ? WHERE id = ?", (new_name, label_id))
            self.conn.commit()
            return self.c.rowcount > 0
        except sqlite3.Error as e:
            raise CustomException(f"Error updating label: {e}")

    def delete_label(self, label_id):
        """
        Delete a label from the database.
        
        Args:
            label_id (str): Label ID to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            self.c.execute("DELETE FROM labels WHERE id = ?", (label_id,))
            self.conn.commit()
            return self.c.rowcount > 0
        except sqlite3.Error as e:
            raise CustomException(f"Error deleting label: {e}")

    def get_labels_by_pattern(self, pattern):
        """
        Get labels that match a pattern.
        
        Args:
            pattern (str): Pattern to search for in label names
            
        Returns:
            list: List of matching label dictionaries
        """
        try:
            self.c.execute("SELECT * FROM labels WHERE name LIKE ?", [f"%{pattern}%"])
            rows = self.c.fetchall()
            labels = []
            for row in rows:
                labels.append({"id": row[0], "name": row[1]})
            return labels
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching labels by pattern: {e}")

    def get_label_count(self):
        """
        Get total number of labels in the database.
        
        Returns:
            int: Number of labels
        """
        try:
            self.c.execute("SELECT COUNT(*) FROM labels")
            return self.c.fetchone()[0]
        except sqlite3.Error as e:
            raise CustomException(f"Error getting label count: {e}")

    def batch_insert_labels(self, labels):
        """
        Batch insert multiple labels for better performance.
        
        Args:
            labels (list): List of label dictionaries to insert
            
        Returns:
            list: List of inserted labels
        """
        try:
            if not labels:
                return []
            
            # Prepare data for batch insert
            label_data = []
            for label in labels:
                label_data.append((label.get("id"), label.get("name")))
            
            # Use executemany for batch insert
            self.c.executemany("""
                INSERT OR IGNORE INTO labels (id, name)
                VALUES (?, ?)
            """, label_data)
            
            self.conn.commit()
            return labels
        except sqlite3.Error as e:
            raise CustomException(f"Error batch inserting labels: {e}")

    def clear_all_labels(self):
        """
        Clear all labels from the database.
        Useful for refreshing label mappings.
        
        Returns:
            bool: True if operation was successful
        """
        try:
            self.c.execute("DELETE FROM labels")
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            raise CustomException(f"Error clearing labels: {e}")

    def get_labels_mapping(self):
        """
        Get labels as a dictionary mapping name to ID.
        
        Returns:
            dict: Dictionary mapping label names to IDs
        """
        try:
            labels = self.get_all_labels()
            return {label["name"]: label["id"] for label in labels}
        except Exception as e:
            raise CustomException(f"Error getting labels mapping: {e}")

    def get_labels_by_ids(self, label_ids):
        """
        Get multiple labels by their IDs.
        
        Args:
            label_ids (list): List of label IDs to fetch
            
        Returns:
            list: List of label dictionaries
        """
        try:
            if not label_ids:
                return []
            
            placeholders = ",".join("?" * len(label_ids))
            self.c.execute(f"SELECT * FROM labels WHERE id IN ({placeholders})", label_ids)
            rows = self.c.fetchall()
            
            labels = []
            for row in rows:
                labels.append({"id": row[0], "name": row[1]})
            return labels
        except sqlite3.Error as e:
            raise CustomException(f"Error fetching labels by IDs: {e}")

    def search_labels(self, search_term):
        """
        Search labels by name (case-insensitive).
        
        Args:
            search_term (str): Term to search for
            
        Returns:
            list: List of matching label dictionaries
        """
        try:
            self.c.execute("SELECT * FROM labels WHERE LOWER(name) LIKE LOWER(?)", [f"%{search_term}%"])
            rows = self.c.fetchall()
            
            labels = []
            for row in rows:
                labels.append({"id": row[0], "name": row[1]})
            return labels
        except sqlite3.Error as e:
            raise CustomException(f"Error searching labels: {e}")
