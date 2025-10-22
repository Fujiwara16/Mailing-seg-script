#!/usr/bin/env python3
"""
Test runner for all test suites.
Runs all tests and provides a comprehensive test report.
"""

import unittest
import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from test_database_schema import TestDatabaseSchema
from test_sql import TestSQLRules
from rule_test import TestRuleValidation
from test_integration import TestEmailWorkflowIntegration
from test_error_handling import TestErrorHandling


def run_all_tests():
    """Run all test suites and provide a comprehensive report."""
    print("🚀 Starting Comprehensive Test Suite")
    print("=" * 60)
    print(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test suites
    test_suites = [
        ("Database Schema Tests", TestDatabaseSchema),
        ("SQL Rule Processing Tests", TestSQLRules),
        ("Rule Validation Tests", TestRuleValidation),
        ("Integration Tests", TestEmailWorkflowIntegration),
        ("Error Handling Tests", TestErrorHandling)
    ]
    
    for suite_name, test_class in test_suites:
        print(f"\n📋 Adding {suite_name}...")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTest(suite)
    
    # Run tests
    print(f"\n🧪 Running {test_suite.countTestCases()} total tests...")
    print("-" * 60)
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    end_time = time.time()
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"⏱️  Duration: {end_time - start_time:.2f} seconds")
    
    # Success rate
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Detailed failure report
    if failures > 0 or errors > 0:
        print("\n" + "=" * 60)
        print("❌ FAILURE DETAILS")
        print("=" * 60)
        
        for test, traceback in result.failures:
            print(f"\n🔴 FAILED: {test}")
            print(f"Traceback: {traceback}")
        
        for test, traceback in result.errors:
            print(f"\n💥 ERROR: {test}")
            print(f"Traceback: {traceback}")
    
    # Performance insights
    if passed > 0:
        avg_time_per_test = (end_time - start_time) / total_tests
        print(f"\n⏱️  Average time per test: {avg_time_per_test:.3f} seconds")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if success_rate == 100:
        print("🎉 All tests passed! Your codebase is in excellent condition.")
        print("✅ Ready for production deployment.")
    elif success_rate >= 90:
        print("👍 Good test coverage! Address the failing tests before deployment.")
    elif success_rate >= 75:
        print("⚠️  Moderate test coverage. Consider fixing failing tests.")
    else:
        print("🚨 Low test coverage. Significant issues need attention.")
    
    if failures > 0 or errors > 0:
        print("\n🔧 Next Steps:")
        print("1. Review and fix failing tests")
        print("2. Run individual test suites to isolate issues")
        print("3. Check test data and mock configurations")
    
    print(f"\nTest run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return result.wasSuccessful()


def run_specific_test_suite(suite_name):
    """Run a specific test suite."""
    suite_mapping = {
        "database": TestDatabaseSchema,
        "sql": TestSQLRules,
        "rules": TestRuleValidation,
        "integration": TestEmailWorkflowIntegration,
        "errors": TestErrorHandling
    }
    
    if suite_name not in suite_mapping:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_mapping.keys())}")
        return False
    
    print(f"🧪 Running {suite_name} test suite...")
    suite = unittest.TestLoader().loadTestsFromTestCase(suite_mapping[suite_name])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test suite
        suite_name = sys.argv[1]
        success = run_specific_test_suite(suite_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
