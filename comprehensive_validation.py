#!/usr/bin/env python3
"""
Comprehensive validation script for AI-GATE project.
This can be run locally to verify all components are in place and syntactically correct.
"""

import os
import sys
import json
import py_compile
import tempfile
from pathlib import Path
from typing import List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.resolve()


class Validator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0

    def check_file_exists(self, path: str, description: str) -> bool:
        """Check if a file exists."""
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            self.passed += 1
            print(f"✓ {description}: {path}")
            return True
        else:
            self.errors.append(f"Missing: {path}")
            print(f"✗ {description}: {path}")
            return False

    def check_dir_exists(self, path: str, description: str) -> bool:
        """Check if a directory exists."""
        full_path = PROJECT_ROOT / path
        if full_path.is_dir():
            self.passed += 1
            print(f"✓ {description}: {path}")
            return True
        else:
            self.errors.append(f"Missing directory: {path}")
            print(f"✗ {description}: {path}")
            return False

    def check_python_syntax(self, path: str, description: str) -> bool:
        """Check Python file syntax."""
        full_path = PROJECT_ROOT / path
        try:
            py_compile.compile(str(full_path), doraise=True)
            self.passed += 1
            print(f"✓ Syntax OK: {path}")
            return True
        except py_compile.PyCompileError as e:
            self.errors.append(f"Syntax error in {path}: {e}")
            print(f"✗ Syntax error: {path}")
            return False

    def check_imports(self, path: str, description: str) -> bool:
        """Check if imports in a file are valid (relative imports)."""
        full_path = PROJECT_ROOT / path
        try:
            with open(full_path) as f:
                content = f.read()
            
            # Check for incorrect relative imports
            if "from base import" in content:
                self.errors.append(f"Invalid relative import in {path}: 'from base import' should be 'from .base import'")
                print(f"✗ Invalid import: {path}")
                return False
            
            self.passed += 1
            print(f"✓ Imports OK: {path}")
            return True
        except Exception as e:
            self.errors.append(f"Error checking imports in {path}: {e}")
            print(f"✗ Import check failed: {path}")
            return False

    def check_json_file(self, path: str, description: str) -> bool:
        """Validate JSON file format."""
        full_path = PROJECT_ROOT / path
        try:
            with open(full_path) as f:
                json.load(f)
            self.passed += 1
            print(f"✓ Valid JSON: {path}")
            return True
        except Exception as e:
            self.errors.append(f"Invalid JSON in {path}: {e}")
            print(f"✗ Invalid JSON: {path}")
            return False

    def check_yaml_file(self, path: str, description: str) -> bool:
        """Check if YAML file exists (basic check, no parsing)."""
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            self.passed += 1
            print(f"✓ YAML file exists: {path}")
            return True
        else:
            self.errors.append(f"Missing YAML: {path}")
            print(f"✗ YAML file missing: {path}")
            return False

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"\n✓ Passed checks: {self.passed}")
        if self.warnings:
            print(f"⚠ Warnings: {len(self.warnings)}")
            for w in self.warnings:
                print(f"  - {w}")
        if self.errors:
            print(f"\n✗ Errors: {len(self.errors)}")
            for e in self.errors:
                print(f"  - {e}")
            return False
        else:
            print("\n✅ All validation checks passed!")
            return True


def main():
    print("=" * 70)
    print("AI-GATE PROJECT VALIDATION")
    print("=" * 70)
    print()

    validator = Validator()

    # === PHASE 1: Directory Structure ===
    print("\n[PHASE 1] Directory Structure")
    print("-" * 70)
    validator.check_dir_exists("gatewayd", "Gateway service directory")
    validator.check_dir_exists("ssh-gw", "SSH gateway directory")
    validator.check_dir_exists("ssh-gw/wrappers", "CLI wrappers directory")
    validator.check_dir_exists("config", "Configuration directory")
    validator.check_dir_exists("examples", "Examples directory")
    validator.check_dir_exists("tests", "Tests directory")

    # === PHASE 2: Core Modules ===
    print("\n[PHASE 2] Core Gateway Modules")
    print("-" * 70)
    validator.check_file_exists("gatewayd/__init__.py", "Gateway package init")
    validator.check_file_exists("gatewayd/__main__.py", "Gateway module entry point")
    validator.check_python_syntax("gatewayd/app.py", "Main Flask app")
    validator.check_python_syntax("gatewayd/auth.py", "Session management")
    validator.check_python_syntax("gatewayd/proxy.py", "HTTP proxy")
    validator.check_python_syntax("gatewayd/credentials.py", "Credential broker")
    validator.check_python_syntax("gatewayd/policy.py", "Policy engine")
    validator.check_python_syntax("gatewayd/approvals.py", "Approval orchestrator")

    # === PHASE 3: SSH Gateway ===
    print("\n[PHASE 3] SSH Gateway")
    print("-" * 70)
    validator.check_file_exists("ssh-gw/__init__.py", "SSH-gw package init")
    validator.check_python_syntax("ssh-gw/dispatcher.py", "SSH command dispatcher")
    validator.check_file_exists("ssh-gw/wrappers/__init__.py", "Wrappers package init")
    validator.check_python_syntax("ssh-gw/wrappers/base.py", "Wrapper base class")

    # Check all CLI wrappers
    wrappers = [
        "aws_wrapper.py",
        "gh_wrapper.py",
        "terraform_wrapper.py",
        "kubectl_wrapper.py",
        "gcloud_wrapper.py",
        "curl_wrapper.py",
        "datadog_wrapper.py",
        "linear_wrapper.py",
    ]
    for wrapper in wrappers:
        wrapper_path = f"ssh-gw/wrappers/{wrapper}"
        validator.check_python_syntax(wrapper_path, f"Wrapper: {wrapper}")
        validator.check_imports(wrapper_path, f"Imports in {wrapper}")

    # === PHASE 4: Configuration ===
    print("\n[PHASE 4] Configuration Files")
    print("-" * 70)
    validator.check_json_file("config/credentials.json", "Credentials config")
    validator.check_json_file("config/enrollments.json", "Enrollments config")
    validator.check_json_file("config/policies.json", "Policies config")
    validator.check_yaml_file("config/gateway.yaml", "Gateway YAML config")
    validator.check_python_syntax("config/init_credentials.py", "Credential initialization")

    # === PHASE 5: Docker ===
    print("\n[PHASE 5] Docker Configuration")
    print("-" * 70)
    validator.check_file_exists("Dockerfile.gatewayd", "Gateway Dockerfile")
    validator.check_file_exists("Dockerfile.ssh-gw", "SSH-gw Dockerfile")
    validator.check_file_exists("Dockerfile.agent", "Agent Dockerfile")
    validator.check_file_exists("docker-compose.yml", "Docker Compose config")
    validator.check_file_exists("requirements.txt", "Python requirements")

    # === PHASE 6: Examples ===
    print("\n[PHASE 6] Example Scripts")
    print("-" * 70)
    examples = [
        "examples/create_session.py",
        "examples/read_request.py",
        "examples/write_request.py",
        "examples/approval_example.py",
    ]
    for example in examples:
        validator.check_python_syntax(example, f"Example: {Path(example).name}")

    # === PHASE 7: Tests ===
    print("\n[PHASE 7] Test Files")
    print("-" * 70)
    tests = [
        "tests/test_policy.py",
        "tests/test_auth.py",
        "tests/test_approvals.py",
        "tests/run_tests.sh",
    ]
    for test in tests:
        if test.endswith(".sh"):
            validator.check_file_exists(test, f"Test script: {Path(test).name}")
        else:
            validator.check_python_syntax(test, f"Test: {Path(test).name}")

    # === PHASE 8: Documentation ===
    print("\n[PHASE 8] Documentation Files")
    print("-" * 70)
    docs = [
        "README.md",
        "DESIGN.md",
        "GETTING_STARTED.md",
        "ARCHITECTURE.md",
        "DEVELOPMENT.md",
        "TROUBLESHOOTING.md",
        "IMPLEMENTATION.md",
        "COMPLETION.md",
        ".github/copilot-instructions.md",
    ]
    for doc in docs:
        validator.check_file_exists(doc, f"Documentation: {Path(doc).name}")

    # === Final Summary ===
    success = validator.print_summary()
    print("\n" + "=" * 70)
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
