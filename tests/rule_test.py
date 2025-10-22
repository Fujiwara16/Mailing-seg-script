import unittest
import json
import os
import sys
from unittest.mock import patch, mock_open

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the rules_service module directly
try:
    from services.rules_service import (
        validate_rules, 
        validate_rule_group, 
        validate_individual_condition,
        validate_actions,
        load_and_validate_rules,
        VALID_FIELDS,
        VALID_STRING_PREDICATES,
        VALID_DATE_PREDICATES,
        VALID_RULE_PREDICATES,
        VALID_ACTIONS
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping tests due to missing dependencies")
    sys.exit(0)
from utils.exception import CustomException


class TestRuleValidation(unittest.TestCase):
    """Test cases for rule validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_rule_group = {
            "name": "Test Rule",
            "predicate": "any",
            "conditions": [
                {
                    "field": "subject",
                    "predicate": "contains",
                    "value": "test"
                }
            ],
            "actions": {
                "mark_as_read": True
            }
        }
        
        self.valid_rules_data = [self.valid_rule_group]
    
    def test_validate_rules_valid_data(self):
        """Test validation with valid rules data."""
        result = validate_rules(self.valid_rules_data)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["errors"]), 0)
    
    def test_validate_rules_invalid_data_type(self):
        """Test validation with invalid data type."""
        with self.assertRaises(CustomException) as context:
            validate_rules("not a list")
        self.assertIn("Rules must be a list", str(context.exception))
    
    def test_validate_rules_empty_list(self):
        """Test validation with empty rules list."""
        result = validate_rules([])
        self.assertTrue(result["success"])
        self.assertIn("No rules defined", result["warnings"])
    
    def test_validate_rule_group_missing_predicate(self):
        """Test rule group validation with missing predicate."""
        invalid_group = {"conditions": [], "actions": {}}
        errors = validate_rule_group(invalid_group, 0)
        self.assertIn("Missing required field 'predicate'", errors[0])
    
    def test_validate_rule_group_invalid_predicate(self):
        """Test rule group validation with invalid predicate."""
        invalid_group = {
            "predicate": "invalid_predicate",
            "conditions": [],
            "actions": {}
        }
        errors = validate_rule_group(invalid_group, 0)
        self.assertIn("Invalid predicate 'invalid_predicate'", errors[0])
    
    def test_validate_rule_group_missing_conditions(self):
        """Test rule group validation with missing conditions."""
        invalid_group = {
            "predicate": "any",
            "actions": {"mark_as_read": True}
        }
        errors = validate_rule_group(invalid_group, 0)
        self.assertIn("Missing required field 'conditions'", errors[0])
    
    def test_validate_rule_group_missing_actions(self):
        """Test rule group validation with missing actions."""
        invalid_group = {
            "predicate": "any",
            "conditions": [{"field": "subject", "predicate": "contains", "value": "test"}]
        }
        errors = validate_rule_group(invalid_group, 0)
        self.assertIn("Missing required field 'actions'", errors[0])
    
    def test_validate_individual_condition_missing_field(self):
        """Test individual condition validation with missing field."""
        invalid_condition = {
            "predicate": "contains",
            "value": "test"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Missing required field 'field'", errors[0])
    
    def test_validate_individual_condition_invalid_field(self):
        """Test individual condition validation with invalid field."""
        invalid_condition = {
            "field": "invalid_field",
            "predicate": "contains",
            "value": "test"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Invalid field 'invalid_field'", errors[0])
    
    def test_validate_individual_condition_invalid_string_predicate(self):
        """Test individual condition validation with invalid string predicate."""
        invalid_condition = {
            "field": "subject",
            "predicate": "invalid_predicate",
            "value": "test"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Invalid string predicate 'invalid_predicate'", errors[0])
    
    def test_validate_individual_condition_invalid_date_predicate(self):
        """Test individual condition validation with invalid date predicate."""
        invalid_condition = {
            "field": "received",
            "predicate": "invalid_predicate",
            "value": "7"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Invalid date predicate 'invalid_predicate'", errors[0])
    
    def test_validate_individual_condition_empty_value(self):
        """Test individual condition validation with empty value."""
        invalid_condition = {
            "field": "subject",
            "predicate": "contains",
            "value": ""
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Value cannot be empty", errors[0])
    
    def test_validate_individual_condition_invalid_date_value(self):
        """Test individual condition validation with invalid date value."""
        invalid_condition = {
            "field": "received",
            "predicate": "less_than_days",
            "value": "not_a_number"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Date value must be a valid integer", errors[0])
    
    def test_validate_individual_condition_negative_date_value(self):
        """Test individual condition validation with negative date value."""
        invalid_condition = {
            "field": "received",
            "predicate": "less_than_days",
            "value": "-5"
        }
        errors = validate_individual_condition(invalid_condition, 0, 0)
        self.assertIn("Date value must be non-negative", errors[0])
    
    def test_validate_individual_condition_valid_string_condition(self):
        """Test individual condition validation with valid string condition."""
        valid_condition = {
            "field": "subject",
            "predicate": "contains",
            "value": "test"
        }
        errors = validate_individual_condition(valid_condition, 0, 0)
        self.assertEqual(len(errors), 0)
    
    def test_validate_individual_condition_valid_date_condition(self):
        """Test individual condition validation with valid date condition."""
        valid_condition = {
            "field": "received",
            "predicate": "less_than_days",
            "value": "7"
        }
        errors = validate_individual_condition(valid_condition, 0, 0)
        self.assertEqual(len(errors), 0)
    
    def test_validate_actions_invalid_key(self):
        """Test actions validation with invalid key."""
        invalid_actions = {
            "invalid_action": True
        }
        errors = validate_actions(invalid_actions, 0)
        self.assertIn("Invalid action key 'invalid_action'", errors[0])
    
    def test_validate_actions_invalid_boolean_value(self):
        """Test actions validation with invalid boolean value."""
        invalid_actions = {
            "mark_as_read": "not_boolean"
        }
        errors = validate_actions(invalid_actions, 0)
        self.assertIn("Action 'mark_as_read' must be a boolean value", errors[0])
    
    def test_validate_actions_invalid_move_message_value(self):
        """Test actions validation with invalid move_message value."""
        invalid_actions = {
            "move_message": ""
        }
        errors = validate_actions(invalid_actions, 0)
        self.assertIn("Action 'move_message' must be a non-empty string", errors[0])
    
    def test_validate_actions_valid_actions(self):
        """Test actions validation with valid actions."""
        valid_actions = {
            "mark_as_read": True,
            "move_message": "Work"
        }
        errors = validate_actions(valid_actions, 0)
        self.assertEqual(len(errors), 0)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_and_validate_rules_success(self, mock_json_load, mock_file):
        """Test successful loading and validation of rules."""
        mock_json_load.return_value = self.valid_rules_data
        
        result = load_and_validate_rules("test_rules.json")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["rules_data"], self.valid_rules_data)
        mock_file.assert_called_once_with("test_rules.json", 'r')
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_and_validate_rules_file_not_found(self, mock_file):
        """Test loading rules from non-existent file."""
        with self.assertRaises(CustomException) as context:
            load_and_validate_rules("nonexistent.json")
        self.assertIn("Rules file not found", str(context.exception))
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0))
    def test_load_and_validate_rules_invalid_json(self, mock_json_load, mock_file):
        """Test loading rules with invalid JSON."""
        with self.assertRaises(CustomException) as context:
            load_and_validate_rules("invalid.json")
        self.assertIn("Invalid JSON in rules file", str(context.exception))
    
    def test_constants_are_defined(self):
        """Test that all validation constants are properly defined."""
        self.assertIsInstance(VALID_FIELDS, list)
        self.assertIsInstance(VALID_STRING_PREDICATES, list)
        self.assertIsInstance(VALID_DATE_PREDICATES, list)
        self.assertIsInstance(VALID_RULE_PREDICATES, list)
        self.assertIsInstance(VALID_ACTIONS, list)
        
        # Check that constants contain expected values
        self.assertIn("from", VALID_FIELDS)
        self.assertIn("subject", VALID_FIELDS)
        self.assertIn("contains", VALID_STRING_PREDICATES)
        self.assertIn("less_than_days", VALID_DATE_PREDICATES)
        self.assertIn("any", VALID_RULE_PREDICATES)
        self.assertIn("mark_as_read", VALID_ACTIONS)


class TestRuleValidationIntegration(unittest.TestCase):
    """Integration tests for rule validation."""
    
    def test_complete_valid_rules_workflow(self):
        """Test complete workflow with valid rules."""
        valid_rules = [
            {
                "name": "Test Rule Group",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "subject",
                        "predicate": "contains",
                        "value": "test"
                    },
                    {
                        "field": "received",
                        "predicate": "less_than_days",
                        "value": "7"
                    }
                ],
                "actions": {
                    "mark_as_read": True,
                    "move_message": "Archive"
                }
            }
        ]
        
        result = validate_rules(valid_rules)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["errors"]), 0)
    
    def test_complete_invalid_rules_workflow(self):
        """Test complete workflow with invalid rules."""
        invalid_rules = [
            {
                "predicate": "invalid_predicate",
                "conditions": [
                    {
                        "field": "invalid_field",
                        "predicate": "invalid_predicate",
                        "value": ""
                    }
                ],
                "actions": {
                    "invalid_action": True
                }
            }
        ]
        
        with self.assertRaises(CustomException) as context:
            validate_rules(invalid_rules)
        
        error_message = str(context.exception)
        self.assertIn("Validation failed", error_message)
        self.assertIn("Invalid predicate", error_message)
        self.assertIn("Invalid field", error_message)
        self.assertIn("Invalid string predicate", error_message)
        self.assertIn("Value cannot be empty", error_message)
        self.assertIn("Invalid action key", error_message)


if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestRuleValidation))
    suite.addTest(unittest.makeSuite(TestRuleValidationIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")