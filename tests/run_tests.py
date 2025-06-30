#!/usr/bin/env python3
"""
Test runner for Crypto Helper Bot
Runs all unit tests, integration tests and generates coverage report
"""

import unittest
import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    # Discover and run tests in backend directory
    loader = unittest.TestLoader()
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    suite = loader.discover(backend_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 30)
    print("🎯 UNIT TESTS SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("✅ All unit tests passed!")
        return True
    else:
        print("❌ Some unit tests failed!")
        
        if result.failures:
            print("\n🔴 FAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\n💥 ERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
        
        return False


def run_integration_tests():
    """Run integration tests"""
    print("\n🌐 Running Integration Tests")
    print("=" * 50)
    
    test_dir = Path(__file__).parent
    integration_tests = [
        'test_api_integration.py',
        'test_real_api.py', 
        'test_cross_rates.py'
    ]
    
    results = []
    
    for test_file in integration_tests:
        test_path = test_dir / test_file
        if test_path.exists():
            print(f"\n🔧 Running {test_file}...")
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)],
                    cwd=str(test_dir),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print(f"✅ {test_file}: PASSED")
                    results.append(True)
                else:
                    print(f"❌ {test_file}: FAILED")
                    print(f"Error output: {result.stderr}")
                    results.append(False)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file}: TIMEOUT")
                results.append(False)
            except Exception as e:
                print(f"💥 {test_file}: ERROR - {e}")
                results.append(False)
        else:
            print(f"⚠️  {test_file}: NOT FOUND")
            results.append(False)
    
    print("\n" + "=" * 30)
    print("🎯 INTEGRATION TESTS SUMMARY")
    passed = sum(results)
    total = len(results)
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("✅ All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed!")
        return False


def run_all_tests():
    """Run all tests (unit + integration)"""
    print("🚀 Running All Crypto Helper Bot Tests")
    print("=" * 60)
    
    # Run unit tests
    unit_success = run_unit_tests()
    
    # Run integration tests
    integration_success = run_integration_tests()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if unit_success and integration_success:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
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
        arg = sys.argv[1]
        if arg == 'unit':
            # Run only unit tests
            success = run_unit_tests()
            exit_code = 0 if success else 1
        elif arg == 'integration':
            # Run only integration tests
            success = run_integration_tests()
            exit_code = 0 if success else 1
        else:
            # Run specific test module
            exit_code = run_specific_test(arg)
    else:
        # Run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)