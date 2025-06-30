#!/usr/bin/env python3
"""
Test runner for Crypto Helper Bot
Runs all unit tests and generates coverage report
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all unit tests"""
    print("🧪 Running Crypto Helper Bot Unit Tests")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        
        if result.failures:
            print("\n🔴 FAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\n💥 ERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
        
        return 1


def run_specific_test(test_module):
    """Run a specific test module"""
    print(f"🧪 Running {test_module} tests")
    print("=" * 50)
    
    suite = unittest.TestLoader().loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_module = sys.argv[1]
        exit_code = run_specific_test(test_module)
    else:
        # Run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)