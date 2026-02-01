#!/usr/bin/env python3
"""Validate all Python files for syntax errors."""

import py_compile
import sys
from pathlib import Path

errors = []
files_checked = 0

print("Validating Python syntax for all files...")
print()

for py_file in Path(".").rglob("*.py"):
    # Skip certain directories
    if any(skip in str(py_file) for skip in [".git", "__pycache__", ".venv", "venv"]):
        continue
    
    files_checked += 1
    try:
        py_compile.compile(str(py_file), doraise=True)
        print(f"✓ {py_file}")
    except py_compile.PyCompileError as e:
        print(f"✗ {py_file}")
        errors.append((py_file, str(e)))

print()
print(f"Checked {files_checked} files")

if errors:
    print(f"\n❌ Found {len(errors)} syntax error(s):\n")
    for file, error in errors:
        print(f"{file}:")
        print(f"  {error}\n")
    sys.exit(1)
else:
    print("✅ All Python files have valid syntax!")
    sys.exit(0)
