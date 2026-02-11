#!/bin/bash

# Test runner - validates all modules can be imported
set -e

echo "Running AI-GATE validation tests..."
echo

# Check Python version
python3 --version

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run unit tests
echo "Running unit tests..."
bash tests/run_tests.sh

echo
echo "✓ All validation tests passed!"
echo

# Try to import the main app
echo "Testing gatewayd import..."
python3 -c "
import sys
sys.path.insert(0, '.')
from gatewayd.app import create_app
app = create_app()
print('✓ gatewayd imports successfully')
print('✓ Flask app created successfully')
"

echo
echo "✓ All components are working!"
