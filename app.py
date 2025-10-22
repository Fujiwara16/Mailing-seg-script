
from services import crud_service
from repository.sql_db import SqlDb
from services.rules_service import apply_rules, load_and_validate_rules
from utils.exception import CustomException
from services.crud_service import CrudService
from services.gmail_service import GmailService
from services.port_cleanup_service import cleanup_port_5001

def apply_rules_to_messages(crud_service):
    validation_result = load_and_validate_rules("rules.json")
    if not validation_result.get("success"):
        print(f"Error: {validation_result.errors}")
        return
    rules_data = validation_result.get("rules_data")
    apply_rules(crud_service, rules_data)

if __name__ == "__main__":
    try:
        print("🚀 Starting HappyFox Email Management System...")

        # Clean up port 5001 before starting OAuth flow
        if not cleanup_port_5001():
            print("❌ Could not free port 5001. Please manually kill processes using this port.")
            print("💡 Try: lsof -ti :5001 | xargs kill -9")
            exit(1)

        # Initialize database and services
        db = SqlDb("emails.db")
        gmail_service = GmailService()
        crud_service = CrudService(gmail_service, db)
        # Update labels mapping
        print("🏷️  Updating labels mapping...")
        labels_mapping = crud_service.update_labels_mapping()
        # Fetch and store emails
        print("📧 Fetching emails from Gmail...")
        crud_service.get_emails_and_store_in_db()
        # Apply rules to emails
        print("🔍 Applying rules to emails...")
        apply_rules_to_messages(crud_service)
        print("✅ Email processing complete!")
    except CustomException as e:
        print(f"❌ Error: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if 'db' in locals():
            db.close()