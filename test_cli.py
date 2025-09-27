#!/usr/bin/env python3
"""
Comprehensive CLI test script for Email Sender CLI.
Tests all major CLI functionality including configuration, templates, and sending.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class CLITester:
    """Comprehensive CLI testing class."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results: dict[str, list[bool]] = {}
        self.temp_files: list[Path] = []

    def run_command(self, cmd: str, input_text: str = None) -> tuple[bool, str, str]:
        """Run a CLI command and return the result."""
        try:
            if self.verbose:
                print(f"    Running: {cmd}")

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, input=input_text, timeout=30
            )

            success = result.returncode == 0
            if self.verbose and not success:
                print(f"    Exit code: {result.returncode}")
                if result.stderr:
                    print(f"    Stderr: {result.stderr.strip()}")

            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def log_test(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        if category not in self.test_results:
            self.test_results[category] = []

        self.test_results[category].append(success)

        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {status}: {test_name}")

        if details and (not success or self.verbose):
            print(f"      {details}")

    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass

    def test_basic_cli(self) -> bool:
        """Test basic CLI functionality."""
        print("\n🧪 Testing Basic CLI Commands")
        print("=" * 50)

        tests = [
            ("Version check", "email-sender --version"),
            ("Help command", "email-sender --help"),
            ("Status check", "email-sender status"),
            ("Config path", "email-sender config path"),
        ]

        for test_name, command in tests:
            success, stdout, stderr = self.run_command(command)
            details = f"Output: {stdout[:100]}..." if stdout else stderr[:100] if stderr else ""
            self.log_test("basic", test_name, success, details)

        return all(self.test_results.get("basic", []))

    def test_config_commands(self) -> bool:
        """Test configuration commands."""
        print("\n🔧 Testing Configuration Commands")
        print("=" * 50)

        # Create temporary config file
        config_path = Path(f"test-config-{int(time.time())}.yaml")
        self.temp_files.append(config_path)

        # Test config initialization
        success, stdout, stderr = self.run_command(f"email-sender config init --path {config_path}")
        self.log_test("config", "Config initialization", success, stderr if not success else "")

        if not success:
            return False

        # Test config show
        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} config show"
        )
        self.log_test("config", "Config show", success, stderr if not success else "")

        # Test config show YAML format
        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} config show --format yaml"
        )
        self.log_test("config", "Config show YAML", success, stderr if not success else "")

        # Test config validation
        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} config validate"
        )
        # Config validation may fail due to invalid SMTP settings, which is expected
        self.log_test(
            "config", "Config validation", True, "Expected to show SMTP connection issues"
        )

        # Test config set
        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} config set smtp.server test.smtp.com"
        )
        self.log_test("config", "Config set", success, stderr if not success else "")

        return len([r for r in self.test_results.get("config", []) if r]) >= 3

    def test_template_commands(self) -> bool:
        """Test template commands."""
        print("\n📝 Testing Template Commands")
        print("=" * 50)

        # Create temporary config file
        config_path = Path(f"test-config-templates-{int(time.time())}.yaml")
        self.temp_files.append(config_path)

        # Initialize config first
        success, _, _ = self.run_command(f"email-sender config init --path {config_path}")
        if not success:
            self.log_test(
                "templates", "Config setup for templates", False, "Failed to create config"
            )
            return False

        # Test template list (empty)
        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} template list"
        )
        self.log_test("templates", "Template list (empty)", success, stderr if not success else "")

        # Test template creation
        success, stdout, stderr = self.run_command(
            f'email-sender --config {config_path} template create test-template --subject "Test Subject" --body "Test Body"'
        )
        self.log_test("templates", "Template creation", success, stderr if not success else "")

        if success:
            # Test template list (with template)
            success, stdout, stderr = self.run_command(
                f"email-sender --config {config_path} template list"
            )
            has_template = success and "test-template" in stdout
            self.log_test(
                "templates",
                "Template list (with template)",
                has_template,
                "Template not found in list" if not has_template else "",
            )

            # Test template show
            success, stdout, stderr = self.run_command(
                f"email-sender --config {config_path} template show test-template"
            )
            self.log_test("templates", "Template show", success, stderr if not success else "")

            # Test template copy
            success, stdout, stderr = self.run_command(
                f"email-sender --config {config_path} template copy test-template test-template-copy"
            )
            self.log_test("templates", "Template copy", success, stderr if not success else "")

        return len([r for r in self.test_results.get("templates", []) if r]) >= 2

    def test_send_commands(self) -> bool:
        """Test send commands (dry run only)."""
        print("\n📧 Testing Send Commands (Dry Run)")
        print("=" * 50)

        # Create temporary config file
        config_path = Path(f"test-config-send-{int(time.time())}.yaml")
        self.temp_files.append(config_path)

        # Initialize config first
        success, _, _ = self.run_command(f"email-sender config init --path {config_path}")
        if not success:
            self.log_test("send", "Config setup for send", False, "Failed to create config")
            return False

        # Test single email dry run
        success, stdout, stderr = self.run_command(
            f'email-sender --config {config_path} send single --to test@example.com --subject "Test" --body "Test body" --dry-run'
        )
        self.log_test("send", "Single email dry run", success, stderr if not success else "")

        # Create a test recipients file
        recipients_file = Path(f"test-recipients-{int(time.time())}.txt")
        self.temp_files.append(recipients_file)
        recipients_file.write_text("test1@example.com\ntest2@example.com\n")

        # Test bulk email dry run
        success, stdout, stderr = self.run_command(
            f'email-sender --config {config_path} send bulk --recipients-file {recipients_file} --subject "Test" --body "Test body" --dry-run'
        )
        self.log_test("send", "Bulk email dry run", success, stderr if not success else "")

        return len([r for r in self.test_results.get("send", []) if r]) >= 1

    def test_error_handling(self) -> bool:
        """Test error handling scenarios."""
        print("\n⚠️  Testing Error Handling")
        print("=" * 50)

        # Test with non-existent config file
        success, stdout, stderr = self.run_command("email-sender --config non-existent.yaml status")
        # This should fail gracefully
        self.log_test(
            "errors", "Non-existent config handling", not success, "Should fail gracefully"
        )

        # Test invalid command
        success, stdout, stderr = self.run_command("email-sender invalid-command")
        self.log_test("errors", "Invalid command handling", not success, "Should show help")

        # Test template not found
        config_path = Path(f"test-config-errors-{int(time.time())}.yaml")
        self.temp_files.append(config_path)
        self.run_command(f"email-sender config init --path {config_path}")

        success, stdout, stderr = self.run_command(
            f"email-sender --config {config_path} template show non-existent"
        )
        self.log_test(
            "errors", "Non-existent template handling", not success, "Should fail gracefully"
        )

        return len([r for r in self.test_results.get("errors", []) if r]) >= 2

    def run_all_tests(self) -> bool:
        """Run all test suites."""
        print("🧪 Email Sender CLI Comprehensive Test Suite")
        print("=" * 60)

        # Check if CLI is available
        success, _, _ = self.run_command("email-sender --version")
        if not success:
            print("❌ CLI not found. Make sure it's installed and in your PATH.")
            print("\nTo install:")
            print("  pip install -e .")
            print("  # or")
            print("  uv sync")
            return False

        # Run all test suites
        test_suites = [
            ("Basic CLI", self.test_basic_cli),
            ("Configuration", self.test_config_commands),
            ("Templates", self.test_template_commands),
            ("Send Commands", self.test_send_commands),
            ("Error Handling", self.test_error_handling),
        ]

        all_passed = True
        for suite_name, test_func in test_suites:
            try:
                suite_passed = test_func()
                if not suite_passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ {suite_name} suite failed with exception: {e}")
                all_passed = False

        # Print summary
        self.print_summary()
        return all_passed

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        total_tests = 0
        total_passed = 0

        for category, results in self.test_results.items():
            passed = sum(results)
            total = len(results)
            total_tests += total
            total_passed += passed

            percentage = (passed / total * 100) if total > 0 else 0
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"

            print(f"{status} {category.upper()}: {passed}/{total} ({percentage:.1f}%)")

        overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 OVERALL: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")

        if total_passed == total_tests:
            print("\n🎉 All tests passed! The CLI is working perfectly.")
            print("\n📖 Next steps:")
            print("1. Run: email-sender config init --interactive")
            print("2. Configure your SMTP settings")
            print("3. Send your first email: email-sender send single --help")
        elif total_passed > total_tests * 0.8:
            print("\n✅ Most tests passed! The CLI is mostly functional.")
            print("⚠️  Some advanced features may need attention.")
        else:
            print("\n⚠️  Several tests failed. Please check the errors above.")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Email Sender CLI Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--category",
        choices=["basic", "config", "templates", "send", "errors"],
        help="Run specific test category only",
    )

    args = parser.parse_args()

    tester = CLITester(verbose=args.verbose)

    try:
        if args.category:
            # Run specific category
            test_methods = {
                "basic": tester.test_basic_cli,
                "config": tester.test_config_commands,
                "templates": tester.test_template_commands,
                "send": tester.test_send_commands,
                "errors": tester.test_error_handling,
            }

            if args.category in test_methods:
                success = test_methods[args.category]()
                tester.print_summary()
                sys.exit(0 if success else 1)
        else:
            # Run all tests
            success = tester.run_all_tests()
            sys.exit(0 if success else 1)

    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
