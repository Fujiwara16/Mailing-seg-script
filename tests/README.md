# HappyFox Test Suite

Comprehensive test suite for the HappyFox Email Management System.

## 📋 Test Coverage

### 🗄️ **Database Tests**
- **`test_database_schema.py`** - Database schema, indexes, and data integrity
- **`test_sql.py`** - SQL-based rule processing and repository operations
- **`rule_test.py`** - Rule validation and configuration

### 🔧 **Service Tests**
- **`test_gmail_service.py`** - Gmail API integration and OAuth
- **`test_integration.py`** - End-to-end workflow testing
- **`test_performance.py`** - Performance and scalability testing
- **`test_error_handling.py`** - Error handling and edge cases

## 🚀 Running Tests

### Run All Tests
```bash
# Run complete test suite
python3 tests/run_all_tests.py

# Run with verbose output
python3 -m unittest discover tests -v
```

### Run Specific Test Suites
```bash
# Database tests
python3 tests/run_all_tests.py database

# SQL rule processing
python3 tests/run_all_tests.py sql

# Gmail service tests
python3 tests/run_all_tests.py gmail

# Integration tests
python3 tests/run_all_tests.py integration

# Performance tests
python3 tests/run_all_tests.py performance

# Error handling tests
python3 tests/run_all_tests.py errors
```

### Run Individual Test Files
```bash
# Database schema tests
python3 tests/test_database_schema.py -v

# SQL rule processing tests
python3 tests/test_sql.py -v

# Gmail service tests
python3 tests/test_gmail_service.py -v

# Integration tests
python3 tests/test_integration.py -v

# Performance tests
python3 tests/test_performance.py -v

# Error handling tests
python3 tests/test_error_handling.py -v
```

## 📊 Test Categories

### **Unit Tests**
- Individual component testing
- Mock external dependencies
- Fast execution
- Isolated functionality

### **Integration Tests**
- End-to-end workflow testing
- Service interaction testing
- Real database operations
- Complete system validation

### **Performance Tests**
- Large dataset processing
- SQL optimization verification
- Memory efficiency testing
- Scalability benchmarks

### **Error Handling Tests**
- Edge case validation
- Error recovery testing
- Invalid input handling
- System resilience

## 🎯 Test Features

### **Comprehensive Coverage**
- ✅ Database schema and integrity
- ✅ SQL-based rule processing
- ✅ Gmail API integration
- ✅ End-to-end workflows
- ✅ Performance optimization
- ✅ Error handling and recovery

### **Realistic Test Data**
- Mock Gmail service with realistic responses
- Large dataset simulation (1000+ emails)
- Various email characteristics and patterns
- Unicode and special character support

### **Performance Validation**
- SQL optimization verification
- Memory efficiency testing
- Concurrent operation testing
- Scalability benchmarks

### **Error Resilience**
- Database connection failures
- Gmail API rate limiting
- Invalid rule configurations
- Network timeout handling

## 📈 Test Metrics

### **Expected Performance**
- Database operations: < 1 second
- Rule processing: < 5 seconds (1000 emails)
- Index creation: < 5 seconds
- Memory usage: Optimized with SQL

### **Test Coverage Goals**
- Unit tests: 90%+ coverage
- Integration tests: Critical paths
- Performance tests: Large datasets
- Error tests: Edge cases

## 🔧 Test Configuration

### **Test Environment**
- Temporary databases for isolation
- Mock services for external dependencies
- Cleanup after each test
- No side effects on production data

### **Test Data**
- Realistic email datasets
- Various sender domains and patterns
- Different date ranges and labels
- Unicode and special characters

## 🚨 Troubleshooting

### **Common Issues**

#### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/happyfox
python3 tests/run_all_tests.py
```

#### Database Errors
```bash
# Clean up any leftover test databases
rm -f test_*.db
```

#### Permission Errors
```bash
# Ensure test files are executable
chmod +x tests/*.py
```

### **Test Debugging**
```bash
# Run with detailed output
python3 -m unittest tests.test_database_schema -v

# Run specific test method
python3 -m unittest tests.test_database_schema.TestDatabaseSchema.test_table_creation -v
```

## 📝 Adding New Tests

### **Test Structure**
```python
import unittest
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        # Setup test fixtures
        
    def tearDown(self):
        # Cleanup after tests
        
    def test_your_functionality(self):
        # Test implementation
        self.assertEqual(actual, expected)
```

### **Best Practices**
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Clean up resources
- Add performance assertions where relevant

## 🎉 Test Results

### **Success Criteria**
- All tests pass
- Performance benchmarks met
- No memory leaks
- Error handling works correctly

### **Continuous Integration**
- Run tests before commits
- Monitor performance regressions
- Validate new features
- Ensure system stability

---

**Happy Testing! 🧪✨**
