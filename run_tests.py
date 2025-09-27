#!/usr/bin/env python3
"""
Test runner script for the email sender CLI.

This script provides convenient ways to run different types of tests
with proper configuration and reporting.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        _result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - FAILED (command not found)")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Email Sender CLI Test Runner")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "cli", "all", "fast", "slow"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-n", type=int, help="Run tests in parallel (number of workers)"
    )
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")

    args = parser.parse_args()

    print("🧪 Email Sender CLI Test Suite")
    print("=" * 60)

    # Check if pytest is available
    try:
        import pytest

        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not found. Install with: uv sync --extra test")
        sys.exit(1)

    # Base pytest command using uv
    cmd = ["uv", "run", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.extend(["-v", "-s"])

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add coverage if requested
    if args.coverage:
        cmd.extend(
            [
                "--cov=cli",
                "--cov=config",
                "--cov=core",
                "--cov=infrastructure",
                "--cov=models",
                "--cov-report=term-missing",
            ]
        )

        if args.html_report:
            cmd.append("--cov-report=html:htmlcov")

    # Add test selection based on type
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "cli":
        cmd.extend(["-m", "cli"])
    elif args.type == "fast":
        cmd.extend(["-m", "not slow"])
    elif args.type == "slow":
        cmd.extend(["-m", "slow"])
    elif args.type == "all":
        pass  # Run all tests

    # Add test directory
    cmd.append("tests/")

    # Run the tests
    success = run_command(cmd, f"Running {args.type} tests")

    if success:
        print("\n🎉 All tests passed!")

        if args.coverage and args.html_report:
            print(f"\n📊 Coverage report generated: {Path.cwd() / 'htmlcov' / 'index.html'}")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


def run_quick_tests():
    """Run a quick subset of tests for development."""
    print("🚀 Running quick tests (unit tests only)")
    cmd = ["uv", "run", "pytest", "-m", "not slow and not integration", "--tb=short", "tests/"]

    return run_command(cmd, "Quick tests")


def run_full_suite():
    """Run the full test suite with coverage."""
    print("🔬 Running full test suite with coverage")
    cmd = [
        "uv",
        "run",
        "pytest",
        "--cov=cli",
        "--cov=config",
        "--cov=core",
        "--cov=infrastructure",
        "--cov=models",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "-v",
        "tests/",
    ]

    return run_command(cmd, "Full test suite")


def check_code_quality():
    """Run code quality checks."""
    print("🔍 Running code quality checks")

    checks = [
        (["uv", "run", "ruff", "check", "."], "Ruff linting"),
        (["uv", "run", "ruff", "format", "--check", "."], "Ruff formatting"),
    ]

    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False

    return all_passed


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments, show options
        print("🧪 Email Sender CLI Test Runner")
        print("=" * 60)
        print("\nQuick options:")
        print("  python run_tests.py --type unit      # Run unit tests only")
        print("  python run_tests.py --type fast      # Run fast tests")
        print("  python run_tests.py --coverage       # Run with coverage")
        print("  python run_tests.py --help           # Show all options")
        print("\nPredefined test suites:")

        # Run quick tests by default
        if run_quick_tests():
            print("\n✨ Quick tests passed! Run with --help for more options.")
        else:
            sys.exit(1)
    else:
        main()
