# This service is responsible for fetching emails from the Gmail API and storing them in the database.
from datetime import datetime, timedelta

class CrudService:
    def __init__(self, gmail_service, conn):
        self.gmail_service = gmail_service
        self.conn = conn

    def get_emails_and_store_in_db(self, date_range=3):
        """
        Fetch emails from Gmail and store in database with optimizations.
        Uses parallel processing and batch database operations.
        """
        # Calculate start and end times correctly
        end_time = datetime.now()
        start_time = end_time - timedelta(days=date_range)
        # Convert to epoch seconds (Gmail API expects seconds, not milliseconds)
        start_epoch = int(start_time.timestamp())
        end_epoch = int(end_time.timestamp())
        # Fetch emails with parallel processing
        emails = self.gmail_service.fetch_emails(start_time=start_epoch, end_time=end_epoch)
        
        # Batch insert emails for better performance
        if emails:
            self.conn.batch_insert_emails(emails)
        else:
            print("📭 No emails found for the specified date range")
        
        return emails

    def fetch_emails_from_db(self):
        return self.conn.get_all_emails()

    def move_message_to_folder(self, email_id, to_folder, existing_labels):
        available_labels = self.gmail_service.move_message(self, email_id, to_folder, existing_labels)
        available_labels = "|".join(available_labels)
        self.conn.move_message(email_id, available_labels)
        return email_id

    def mark_as_read(self, message_id):
        self.gmail_service.mark_as_read(message_id)
        self.conn.mark_as_read(message_id)
        return message_id

    def mark_as_unread(self, message_id):
        self.gmail_service.mark_as_unread(message_id)
        self.conn.mark_as_unread(message_id)
        return message_id

    def update_labels_mapping(self):
        labels_dict = self.gmail_service.get_available_labels()
        for label_name, label_id in labels_dict.items():
            # Create proper dictionary for insert_label
            label_data = {"id": label_id, "name": label_name}
            self.insert_label(label_data)
        return labels_dict

    def get_labels_mapping(self):
        return self.conn.get_all_labels()

    def insert_label(self, label_data):
        self.conn.insert_label(label_data)