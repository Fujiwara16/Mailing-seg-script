from services import crud_service
from utils.exception import CustomException
import json

# Valid field names
VALID_FIELDS = ["from", "subject", "message", "received"]

# Valid string predicates
VALID_STRING_PREDICATES = ["contains", "does_not_contain", "equals", "does_not_equal"]

# Valid date predicates
VALID_DATE_PREDICATES = ["less_than_days", "greater_than_days", "less_than_months", "greater_than_months"]

# Valid rule predicates
VALID_RULE_PREDICATES = ["all", "any"]

# Valid actions
VALID_ACTIONS = ["mark_as_read", "mark_as_unread", "move_message"]

def validate_rules(rules_data):
    """
    Validate the rules JSON structure and content.
    
    Args:
        rules_data (list): List of rule objects to validate
        
    Returns:
        dict: Validation result with success status and errors
        
    Raises:
        CustomException: If validation fails
    """
    errors = []
    warnings = []
    
    if not isinstance(rules_data, list):
        raise CustomException("Rules must be a list of rule objects")
    
    if len(rules_data) == 0:
        warnings.append("No rules defined")
        return {"success": True, "errors": [], "warnings": warnings}
    
    for i, rule_group in enumerate(rules_data):
        rule_errors = validate_rule_group(rule_group, i)
        errors.extend(rule_errors)
    
    if errors:
        raise CustomException(f"Validation failed: {'; '.join(errors)}")
    
    return {"success": True, "errors": [], "warnings": warnings}

def validate_rule_group(rule_group, index):
    """
    Validate a single rule group.
    
    Args:
        rule_group (dict): Rule group to validate
        index (int): Index of the rule group
        
    Returns:
        list: List of validation errors
    """
    errors = []
    print("Validating rule group: ", rule_group)
    
    # Check required fields
    required_fields = ["predicate", "conditions", "actions"]
    for field in required_fields:
        if field not in rule_group:
            errors.append(f"Rule group {index}: Missing required field '{field}'")
    
    if errors:
        return errors
    
    # Validate predicate
    predicate = rule_group.get("predicate")
    if predicate not in VALID_RULE_PREDICATES:
        errors.append(f"Rule group {index}: Invalid predicate '{predicate}'. Must be one of {VALID_RULE_PREDICATES}")
    
    # Validate conditions array
    conditions = rule_group.get("conditions", [])
    # Validate each condition
    for j, condition in enumerate(conditions):
        condition_errors = validate_individual_condition(condition, index, j)
        errors.extend(condition_errors)
    # Validate actions
    actions = rule_group.get("actions", {})
    action_errors = validate_actions(actions, index)
    errors.extend(action_errors)
    
    return errors

def load_and_validate_rules(file_path="rules.json"):
    """
    Load and validate rules from JSON file.
    
    Args:
        file_path (str): Path to the rules JSON file
        
    Returns:
        dict: Validation result with success status and rules data
    """
    try:
        with open(file_path, 'r') as f:
            rules_data = json.load(f)
        
        validation_result = validate_rules(rules_data)
        validation_result["rules_data"] = rules_data
        return validation_result
        
    except FileNotFoundError:
        raise CustomException(f"Rules file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise CustomException(f"Invalid JSON in rules file: {e}")
    except Exception as e:
        raise CustomException(f"Error loading rules: {e}")

def apply_rules(crud_service, rules_data):
    """
    Apply rules to emails from the database.
    
    Args:
        crud_service: Crud service object
        rules_data: List of rule groups from rules.json
    """
    from datetime import datetime, timedelta
    
    # Validate rules before processing
    print("🔍 Validating rules before processing...")
    try:
        validation_result = validate_rules(rules_data)
        if not validation_result["success"]:
            raise CustomException("Rules validation failed")
        print("✅ Rules validation passed!")
    except CustomException as e:
        print(f"❌ Rules validation failed: {e}")
        return []
    
    emails = crud_service.fetch_emails_from_db()
    print(f"📧 Processing {len(emails)} emails with {len(rules_data)} rule groups")
    
    for email in emails:
        msg_id = email[0]  # id
        sender = email[1]  # sender
        subject = email[2]  # subject
        snippet = email[3]  # snippet
        received = email[4]  # received
        is_read = email[5]  # is_read
        labels = email[6]  # labels
        
        print(f"\n📧 Processing: {subject[:50]}...")
        
        # Process each rule group
        for rule_group in rules_data:
            rule_group_name = rule_group.get("name", "Unnamed Rule")
            predicate = rule_group.get("predicate", "any")
            conditions = rule_group.get("conditions", [])
            actions = rule_group.get("actions", {})
            
            print(f"🔍 Checking rule group: {rule_group_name} ({predicate})")
            
            # Check if any/all conditions match
            matches = []
            for condition in conditions:
                match = evaluate_condition(condition, sender, subject, snippet, received)
                matches.append(match)
            if match:
                    print(f"✅ Condition matched: {condition.get('field')} {condition.get('predicate')} '{condition.get('value')}'")
            
            # Determine if rule group matches based on predicate
            rule_group_matches = False
            if predicate == "any":
                rule_group_matches = any(matches)
            elif predicate == "all":
                rule_group_matches = all(matches)
            
            # Execute actions if rule group matches
            if rule_group_matches:
                print(f"🎯 Rule group '{rule_group_name}' matched! Executing actions...")
                execute_actions_new(crud_service, msg_id, subject, actions, labels)
            else:
                print(f"❌ Rule group '{rule_group_name}' did not match")

def evaluate_condition(condition, sender, subject, snippet, received):
    """
    Evaluate a single condition against email data.
    
    Args:
        condition: Condition dictionary
        sender: Email sender
        subject: Email subject
        snippet: Email snippet
        received: Email received date
        
    Returns:
        bool: True if condition matches
    """
    field = condition.get("field")
    predicate = condition.get("predicate")
    value = condition.get("value", "")
    
    # Get field value
    if field == "from":
        field_val = sender.lower()
    elif field == "subject":
        field_val = subject.lower()
    elif field == "message":
        field_val = snippet.lower()
    elif field == "received":
        field_val = received
    else:
        return False
    
    # Handle date field differently
    if field == "received":
        return evaluate_date_condition(predicate, value, field_val)
    else:
        return evaluate_string_condition(predicate, value, field_val)

def evaluate_rule(rule, sender, subject, snippet, received):
    """
    Evaluate a single rule against email data.
    
    Args:
        rule: Rule dictionary
        sender: Email sender
        subject: Email subject
        snippet: Email snippet
        received: Email received date
        
    Returns:
        bool: True if rule matches
    """
    field = rule.get("field")
    predicate = rule.get("predicate")
    value = rule.get("value", "")
    
    # Get field value
    if field == "from":
        field_val = sender.lower()
    elif field == "subject":
        field_val = subject.lower()
    elif field == "message":
        field_val = snippet.lower()
    elif field == "received":
        field_val = received
    else:
        return False
    
    # Handle date field differently
    if field == "received":
        return evaluate_date_rule(predicate, value, field_val)
    else:
        return evaluate_string_rule(predicate, value, field_val)

def evaluate_string_rule(predicate, value, field_val):
    """Evaluate string-based rules."""
    value_lower = value.lower()
    
    if predicate == "contains":
        return value_lower in field_val
    elif predicate == "does_not_contain":
        return value_lower not in field_val
    elif predicate == "equals":
        return field_val == value_lower
    elif predicate == "does_not_equal":
        return field_val != value_lower
    else:
        return False

def evaluate_date_rule(predicate, value, field_val):
    """Evaluate date-based rules."""
    try:
        from datetime import datetime, timedelta
        
        # Parse the value (should be number of days)
        days = int(value)
        
        # Parse the received date (assuming it's in ISO format or timestamp)
        if isinstance(field_val, str):
            try:
                # Try parsing as ISO format
                received_date = datetime.fromisoformat(field_val.replace('Z', '+00:00'))
            except:
                # Try parsing as timestamp
                received_date = datetime.fromtimestamp(int(field_val) / 1000)
        else:
            received_date = datetime.fromtimestamp(int(field_val) / 1000)
        
        now = datetime.now()
        time_diff = now - received_date
        
        if predicate == "less_than_days":
            return time_diff.days > days
        elif predicate == "greater_than_days":
            return time_diff.days < days
        elif predicate == "less_than_months":
            return time_diff.days > (days * 30)
        elif predicate == "greater_than_months":
            return time_diff.days < (days * 30)
        else:
            return False
    except Exception as e:
        print(f"⚠️  Error evaluating date rule: {e}")
        return False
        
def execute_actions_new(crud_service, msg_id, subject, actions, existing_labels):
    """
    Execute actions for a matched rule group using the new structure.
    
    Args:
        crud_service: Crud service object
        msg_id: Message ID
        subject: Email subject
        actions: Dictionary of actions to execute
        existing_labels: List of existing labels
    """
    for action_name, action_value in actions.items():
        try:
            if action_name == "mark_as_read" and action_value:
                crud_service.mark_as_read(msg_id)
                print(f"✅ Marked '{subject[:30]}...' as read")
                
            elif action_name == "mark_as_unread" and action_value:
                crud_service.mark_as_unread(msg_id)
                print(f"📩 Marked '{subject[:30]}...' as unread")
                
            elif action_name == "move_message" and action_value:
                folder_name = action_value
                crud_service.move_message_to_folder(msg_id, folder_name, existing_labels)
                print(f"📁 Moved '{subject[:30]}...' to {folder_name}")
            else:
                print(f"⚠️  Unknown action: {action_name} = {action_value}")
                
        except Exception as e:
            print(f"❌ Error executing action '{action_name}': {e}")

def evaluate_string_condition(predicate, value, field_val):
    """Evaluate string-based conditions."""
    value_lower = value.lower()
    
    if predicate == "contains":
        return value_lower in field_val
    elif predicate == "does_not_contain":
        return value_lower not in field_val
    elif predicate == "equals":
        return field_val == value_lower
    elif predicate == "does_not_equal":
        return field_val != value_lower
    else:
        return False

def evaluate_date_condition(predicate, value, field_val):
    """Evaluate date-based conditions."""
    try:
        from datetime import datetime, timedelta
        
        # Parse the value (should be number of days)
        days = int(value)
        
        # Parse the received date (assuming it's in ISO format or timestamp)
        if isinstance(field_val, str):
            try:
                # Try parsing as ISO format
                received_date = datetime.fromisoformat(field_val.replace('Z', '+00:00'))
            except:
                # Try parsing as timestamp
                received_date = datetime.fromtimestamp(int(field_val) / 1000)
        else:
            received_date = datetime.fromtimestamp(int(field_val) / 1000)
        
        now = datetime.now()
        time_diff = now - received_date
        if predicate == "less_than_days":
            return time_diff.days < days
        elif predicate == "greater_than_days":
            return time_diff.days > days
        elif predicate == "less_than_months":
            return time_diff.days < (days * 30)
        elif predicate == "greater_than_months":
            return time_diff.days > (days * 30)
        else:
            return False
            
    except Exception as e:
        print(f"⚠️  Error evaluating date condition: {e}")
        return False

def validate_individual_condition(condition, group_index, condition_index):
    """Validate a single condition."""
    errors = []
    
    # Check if condition is a dictionary
    if not isinstance(condition, dict):
        errors.append(f"Rule group {group_index}, condition {condition_index}: Must be a dictionary")
        return errors
    
    # Check required fields
    field = condition.get("field")
    if not field:
        errors.append(f"Rule group {group_index}, condition {condition_index}: Missing required field 'field'")
    elif field not in VALID_FIELDS:
        errors.append(f"Rule group {group_index}, condition {condition_index}: Invalid field '{field}'. Must be one of: {', '.join(VALID_FIELDS)}")
    
    predicate = condition.get("predicate")
    if not predicate:
        errors.append(f"Rule group {group_index}, condition {condition_index}: Missing required field 'predicate'")
    else:
        # Check predicate based on field type
        if field == "received":
            if predicate not in VALID_DATE_PREDICATES:
                errors.append(f"Rule group {group_index}, condition {condition_index}: Invalid date predicate '{predicate}'. Must be one of: {', '.join(VALID_DATE_PREDICATES)}")
        else:
            if predicate not in VALID_STRING_PREDICATES:
                errors.append(f"Rule group {group_index}, condition {condition_index}: Invalid string predicate '{predicate}'. Must be one of: {', '.join(VALID_STRING_PREDICATES)}")
    
    # Check value
    value = condition.get("value", "")
    if not value:
        errors.append(f"Rule group {group_index}, condition {condition_index}: Value cannot be empty")
    elif field == "received":
        # Validate date value
        try:
            days = int(value)
            if days < 0:
                errors.append(f"Rule group {group_index}, condition {condition_index}: Date value must be non-negative")
        except ValueError:
            errors.append(f"Rule group {group_index}, condition {condition_index}: Date value must be a valid integer")
    
    return errors

def validate_actions(actions, group_index):
    """Validate actions dictionary."""
    errors = []
    
    valid_action_keys = ["mark_as_read", "mark_as_unread", "move_message"]
    
    for action_key, action_value in actions.items():
        if action_key not in valid_action_keys:
            errors.append(f"Rule group {group_index}: Invalid action key '{action_key}'. Must be one of: {', '.join(valid_action_keys)}")
        elif action_key in ["mark_as_read", "mark_as_unread"]:
            if not isinstance(action_value, bool):
                errors.append(f"Rule group {group_index}: Action '{action_key}' must be a boolean value")
        elif action_key == "move_message":
            if not isinstance(action_value, str) or not action_value:
                errors.append(f"Rule group {group_index}: Action 'move_message' must be a non-empty string")
    
    return errors