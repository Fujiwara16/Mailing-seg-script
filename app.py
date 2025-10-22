
import argparse
import os
import time
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

def setup_new_user():
    """
    Delete token.json to force fresh OAuth authentication for new users.
    """
    token_file = "token.json"
    if os.path.exists(token_file):
        try:
            os.remove(token_file)
            print("🗑️  Deleted existing token.json for fresh authentication")
            print("🔐 You will be prompted to re-authenticate with Gmail")
        except Exception as e:
            print(f"⚠️  Warning: Could not delete {token_file}: {e}")
    else:
        print("ℹ️  No existing token.json found - fresh authentication will be required")
    print(f"\n {'-'*50} \n")
    time.sleep(2)

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="HappyFox Email Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python3 app.py                    # Run with existing authentication
        python3 app.py --new-user         # Force fresh OAuth authentication
        """
    )
    
    parser.add_argument(
        "--new-user", 
        action="store_true",
        help="Delete existing token.json and force fresh OAuth authentication"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print("🚀 Starting HappyFox Email Management System...")
        
        # Handle new user setup if requested
        if args.new_user:
            setup_new_user()

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