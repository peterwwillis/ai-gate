#!/bin/bash

# Run all tests
set -e

echo "Running AI-GATE tests..."
echo

echo "Policy engine tests:"
python tests/test_policy.py
echo

echo "Authentication tests:"
python tests/test_auth.py
echo

echo "Approval orchestrator tests:"
python tests/test_approvals.py
echo

echo "All tests passed! ✓"
