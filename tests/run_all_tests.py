#!/usr/bin/env python
"""
Test Runner Script
Runs all test suites with proper categorization and reporting.
"""
import subprocess
import sys
import os


def run_tests(test_type=None, verbose=True):
    """Run tests by type or all tests."""
    base_cmd = ['pytest', '-v']
    
    if test_type:
        if test_type == 'unit':
            base_cmd.extend(['tests/unit'])
        elif test_type == 'integration':
            base_cmd.extend(['tests/integration'])
        elif test_type == 'validation':
            base_cmd.extend(['tests/validation'])
        elif test_type == 'system':
            base_cmd.extend(['tests/system'])
        elif test_type == 'regression':
            base_cmd.extend(['tests/regression'])
        else:
            print(f"Unknown test type: {test_type}")
            return False
    else:
        base_cmd.extend(['tests'])
    
    if verbose:
        base_cmd.append('-v')
    
    print(f"\n{'='*60}")
    print(f"Running {'all tests' if not test_type else test_type + ' tests'}...")
    print(f"{'='*60}\n")
    
    result = subprocess.run(base_cmd)
    return result.returncode == 0


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        success = run_tests(test_type)
    else:
        print("\n" + "="*60)
        print("MediQueue Test Suite Runner")
        print("="*60)
        print("\nAvailable test types:")
        print("  1. unit         - Unit tests")
        print("  2. integration  - Integration tests")
        print("  3. validation   - Validation tests")
        print("  4. system       - System tests")
        print("  5. regression   - Regression tests")
        print("  6. all          - Run all tests")
        print("\nUsage:")
        print("  python tests/run_all_tests.py [test_type]")
        print("  pytest tests/unit              # Run unit tests only")
        print("  pytest tests/integration       # Run integration tests only")
        print("  pytest tests/validation        # Run validation tests only")
        print("  pytest tests/system            # Run system tests only")
        print("  pytest tests/regression        # Run regression tests only")
        print("  pytest tests                   # Run all tests")
        print("="*60 + "\n")
        
        # Run all tests by default
        success = run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

