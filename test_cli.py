#!/usr/bin/env python3
"""
Simple test script to verify CLI functionality.
Run this after setting up your configuration.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a CLI command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def test_cli():
    """Test basic CLI functionality."""
    print("🧪 Testing Email Sender CLI")
    print("=" * 50)

    tests = [
        ("Version check", "email-sender version"),
        ("Help command", "email-sender --help"),
        ("Status check", "email-sender status"),
        ("Config path", "email-sender config path"),
        ("Template list", "email-sender template list"),
    ]

    passed = 0
    total = len(tests)

    for test_name, command in tests:
        print(f"\n📋 {test_name}")
        print(f"   Command: {command}")

        success, stdout, stderr = run_command(command)

        if success:
            print("   ✅ PASSED")
            passed += 1
        else:
            print("   ❌ FAILED")
            if stderr:
                print(f"   Error: {stderr.strip()}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! CLI is working correctly.")
    else:
        print("⚠️  Some tests failed. Check your installation and configuration.")

    return passed == total


def test_config_creation():
    """Test configuration creation."""
    print("\n🔧 Testing Configuration Creation")
    print("=" * 50)

    config_path = Path("test-config.yaml")

    # Clean up any existing test config
    if config_path.exists():
        config_path.unlink()

    # Create test configuration
    success, stdout, stderr = run_command(f"email-sender config init --path {config_path}")

    if success and config_path.exists():
        print("✅ Configuration file created successfully")

        # Show config
        success2, stdout2, stderr2 = run_command(f"email-sender config show --config {config_path}")
        if success2:
            print("✅ Configuration can be read successfully")
        else:
            print("❌ Failed to read configuration")

        # Clean up
        config_path.unlink()
        return success2
    else:
        print("❌ Failed to create configuration file")
        if stderr:
            print(f"Error: {stderr.strip()}")
        return False


def main():
    """Main test function."""
    print("Email Sender CLI Test Suite")
    print("=" * 60)

    # Check if CLI is available
    success, _, _ = run_command("email-sender --version")
    if not success:
        print("❌ CLI not found. Make sure it's installed and in your PATH.")
        print("\nTo install:")
        print("  pip install -e .")
        print("  # or")
        print("  uv sync")
        sys.exit(1)

    # Run tests
    cli_tests_passed = test_cli()
    config_tests_passed = test_config_creation()

    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS")
    print("=" * 60)

    if cli_tests_passed and config_tests_passed:
        print("🎉 All tests passed! The CLI is ready to use.")
        print("\n📖 Next steps:")
        print("1. Run: email-sender config init --interactive")
        print("2. Configure your SMTP settings")
        print("3. Send your first email: email-sender send single --help")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
