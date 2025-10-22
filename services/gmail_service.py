import os
import base64
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from utils.exception import CustomException
import traceback

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailService:
    def __init__(self):
        try:
            creds = None
            try:
                if os.path.exists("token.json"):
                    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            except Exception as e:
                print(f"Error getting credentials: {e}")
                creds = None
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    # Set access_type to 'offline' to get refresh token
                    flow.redirect_uri = 'http://localhost:5001/'
                    try:
                        creds = flow.run_local_server(port=5001, access_type='offline', prompt='consent')
                    except OSError as e:
                        if "Address already in use" in str(e):
                            print("⚠️  Port 5001 is still in use, please wait a moment and try again")
                            raise CustomException("Port 5001 is still in use. Please wait a moment and try again.")
                        else:
                            raise e
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
            self.service = build("gmail", "v1", credentials=creds)
        except Exception as e:
            raise CustomException(f"Error getting Gmail service: {e}")


    def fetch_emails(self, start_time=None, end_time=None, max_results=1000):
        """
        Fetch emails from Gmail API within a specified time range.
        Optimized with threading for parallel processing.

        Args:
            start_time (int, optional): Start time in epoch seconds
            end_time (int, optional): End time in epoch seconds  
            max_results (int): Maximum number of emails to fetch (default: 1000)

        Returns:
            list: List of email dictionaries
        """
        try:
            # Build query for time range
            query_parts = []
            if start_time:
                query_parts.append(f"after:{start_time}")
            if end_time:
                query_parts.append(f"before:{end_time}")
            query = " ".join(query_parts) if query_parts else None
            
            # Prepare request parameters with optimizations
            request_params = {
                "userId": "me",
                "maxResults": min(max_results, 500),  # Gmail API limit
                "includeSpamTrash": False  # Exclude spam/trash for better performance
            }
            if query:
                request_params["q"] = query
                
            # Get message list
            results = self.service.users().messages().list(**request_params).execute()
            messages = results.get("messages", [])
            
            if not messages:
                return []
            
            # Fetch email details in parallel using threading
            emails = self._fetch_emails_parallel(messages)
            print(f"📥 Fetched {len(emails)} emails using parallel processing")
            
            return emails
            
        except Exception as e:
            raise CustomException(f"Error fetching emails: {e}")

    def _fetch_emails_parallel(self, messages):
        """
        Fetch email details in parallel using threading for better performance.
        Uses thread-safe approach with individual service instances.
        """
        emails = []
        
        # Use ThreadPoolExecutor for parallel processing with reduced workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_msg = {
                executor.submit(self._fetch_single_email_safe, msg.get("id")): msg
                for msg in messages
            }

            # Collect results as they complete
            for future in as_completed(future_to_msg):
                try:
                    email_data = future.result()
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    msg = future_to_msg[future]
                    print(f"Error fetching email {msg['id']}: {e}")
                    continue
        
        return emails

    def _fetch_single_email_safe(self, msg_id):
        """
        Thread-safe method to fetch a single email.
        Creates a new service instance for each thread.
        """
        try:
            if not msg_id:
                return None
            # Create a new service instance for thread safety
            service = self._create_new_service()
            # Use optimized parameters to fetch only essential data
            msg_data = service.users().messages().get(
                userId="me", 
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            return self._process_email_data(msg_data)
        except Exception as e:
            print(f"Error fetching email {msg_id}: {e}")
            return None

    def _create_new_service(self):
        """
        The Gmail API client is not actually thread-safe for concurrent operations, even for read operations.
        The SSL connection is getting corrupted when accessed by multiple threads simultaneously.
        So we need to create a new service instance for each thread.

        We did this because processing each email synchronously was taking too long.
        This approach is the better option as gmail api does support multiple connections,
        but not concurrent operations with the same connection.

        Returns:
            service: Gmail service instance
        Raises:
            CustomException: If error creating new service
        """
        try:
            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    flow.redirect_uri = 'http://localhost:5001/'
                    creds = flow.run_local_server(port=5001, access_type='offline', prompt='consent')
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
            
            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            print(f"Error creating new service: {e}")
            return None

    def _process_email_data(self, msg_data):
        """
        Process email data into standardized format.
        """
        try:
            payload = msg_data.get("payload", {})
            headers = payload.get("headers", [])
            
            # Extract headers efficiently
            header_dict = {h.get("name"): h.get("value") for h in headers}
            sender = header_dict.get("From", "")
            subject = header_dict.get("Subject", "")
            
            snippet = msg_data.get("snippet", "")
            internal_date = msg_data.get("internalDate", "")
            labels = msg_data.get("labelIds", [])
            labels_str = "|".join(labels)
            
            # Convert epoch milliseconds to readable format
            received_date = ""
            if internal_date:
                try:
                    from datetime import datetime
                    # Convert from milliseconds to seconds
                    timestamp = int(internal_date) // 1000
                    received_date = datetime.fromtimestamp(timestamp).isoformat()
                except (ValueError, OSError):
                    received_date = internal_date
            
            return {
                "id": msg_data.get("id"),
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "received": received_date,
                "internal_date": internal_date,
                "labels": labels_str
            }
        except Exception as e:
            print(f"Error processing email data: {e}")
            return None

    def mark_as_read(self, msg_id):
        try:
            self.service.users().messages().modify(userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}).execute()
        except Exception as e:
            raise CustomException(f"Error marking email as read: {e}")

    def mark_as_unread(self, msg_id):
        try:
            self.service.users().messages().modify(userId="me", id=msg_id, body={"addLabelIds": ["UNREAD"]}).execute()
        except Exception as e:
            raise CustomException(f"Error marking email as unread: {e}")

    def move_message(self, crud_service, msg_id, to_folder, existing_labels):
        """
        Move an email to a specific folder/label.
        Automatically creates the label if it doesn't exist.
        
        Args:
            crud_service: Crud service object
            msg_id (str): Message ID to move
            to_folder (str): Target folder/label name
            existing_labels (list): List of existing labels
        
        Returns:
            list: List of existing labels
        Note:
            - Standard Gmail labels: INBOX, SPAM, TRASH, SENT, DRAFT (always exist)
            - Custom labels will be created automatically if they don't exist
        """

        # import from crud_service to avoid circular import
        try:
            # Check if label exists, create if it doesn't
            existing_labels = existing_labels.split("|")
            available_labels = crud_service.get_labels_mapping()
            available_label_ids = {label.get('name'): label.get('id') for label in available_labels}
            existing_label_id = available_label_ids.get(to_folder)
            if not existing_label_id:
                print(f"🏷️  Creating new label: {to_folder}")
                created_label = self.create_label(to_folder)
                to_folder = created_label.get('id')
                crud_service.insert_label(created_label)
            else:
                to_folder = existing_label_id

            # If the label is already in the existing labels, return the existing labels
            if to_folder in existing_labels:
                print(f"🏷️  Label {to_folder} is already in the existing labels")
                return existing_labels

            # Prepare label modifications
            remove_labels = []
            add_labels = [to_folder]
            
            # system labels ["CHAT", "SENT", "IMPORTANT", "TRASH", "UNREAD", "DRAFT", "SPAM", "STARRED", "YELLOW_STAR", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
            # these can be configured on the basis of what we want to keep as is in the email labels
            unaltered_system_labels = ["CHAT", "UNREAD", "DRAFT", "IMPORTANT", "STARRED", "TRASH", "SPAM", "SENT"]
            for label in existing_labels:
                if label not in unaltered_system_labels:
                    remove_labels.append(label)
            # Build modification body
            modify_body = {}
            # Update existing_labels array to reflect changes
            if remove_labels:
                for label in remove_labels:
                    if label in existing_labels:
                        existing_labels.remove(label)
                modify_body["removeLabelIds"] = remove_labels

            if add_labels:
                for label in add_labels:
                    if label not in existing_labels:
                        existing_labels.append(label)
                modify_body["addLabelIds"] = add_labels

            self.service.users().messages().modify(userId="me", id=msg_id, body=modify_body).execute()
            print(f"📁 Moved email to {to_folder}")
            return existing_labels
        except Exception as e:
            raise CustomException(f"Error moving email to {to_folder}: {e}, {traceback.format_exc()}")

    def get_available_labels(self):
        """
        Get all available labels in the Gmail account.
        
        Args:
            service: Gmail service object
            
        Returns:
            dict: Dictionary mapping label names to label IDs
        """
        try:
            labels = self.service.users().labels().list(userId="me").execute()
            # added default values to avoid sql insert errors
            return {label.get("name", "N/A"): label.get("id", "N/A") for label in labels.get("labels", [])}
        except Exception as e:
            raise CustomException(f"Error getting labels: {e}")

    def create_label(self, label_name):
        """
        Create a new label in Gmail.
        
        Args:
            service: Gmail service object
            label_name (str): Name of the label to create
            
        Returns:
            dict: Created label information
        """
        try:
            label_object = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }
            created_label = self.service.users().labels().create(userId="me", body=label_object).execute()
            return created_label
        except Exception as e:
            raise CustomException(f"Error creating label {label_name}: {e}")