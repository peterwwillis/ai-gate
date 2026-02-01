#!/bin/bash

# AI-GATE Docker Compose Test & Fix Loop
# This script attempts to run docker-compose up and handles common errors

set -e

ATTEMPT=1
MAX_ATTEMPTS=10

echo "=========================================="
echo "AI-GATE: Docker Compose Test & Fix Loop"
echo "=========================================="
echo

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT of $MAX_ATTEMPTS"
    echo "----------------------------------------"
    
    # Try to run docker-compose up
    if docker compose up --build 2>&1 | tee /tmp/compose_attempt_$ATTEMPT.log; then
        echo
        echo "✅ SUCCESS! docker-compose up completed successfully"
        echo "DONE!"
        exit 0
    else
        EXIT_CODE=$?
        echo
        echo "❌ docker-compose up failed with exit code $EXIT_CODE"
        echo
        
        # Extract last 30 lines of log
        echo "Last 30 lines of output:"
        tail -30 /tmp/compose_attempt_$ATTEMPT.log
        echo
        
        # Check for common errors and attempt fixes
        
        # Error 1: Flask import missing
        if grep -q "ModuleNotFoundError.*flask" /tmp/compose_attempt_$ATTEMPT.log; then
            echo "Issue detected: Flask not installed. Rebuilding..."
            docker compose down -v
            docker compose build --no-cache
            ATTEMPT=$((ATTEMPT + 1))
            continue
        fi
        
        # Error 2: Port already in use
        if grep -q "Address already in use" /tmp/compose_attempt_$ATTEMPT.log; then
            echo "Issue detected: Port in use. Killing existing containers..."
            docker compose down
            sleep 2
            ATTEMPT=$((ATTEMPT + 1))
            continue
        fi
        
        # Error 3: Import errors in Python
        if grep -q "ImportError\|ModuleNotFoundError\|SyntaxError" /tmp/compose_attempt_$ATTEMPT.log; then
            echo "Issue detected: Python import/syntax error"
            
            # Extract the specific error
            ERROR_LINE=$(grep -A2 "ImportError\|ModuleNotFoundError\|SyntaxError" /tmp/compose_attempt_$ATTEMPT.log | head -5)
            echo "Error details:"
            echo "$ERROR_LINE"
            echo
            
            # Common fix: check if __init__.py files exist
            echo "Checking for missing __init__.py files..."
            touch ssh-gw/__init__.py
            touch ssh-gw/wrappers/__init__.py
            
            docker compose build --no-cache
            ATTEMPT=$((ATTEMPT + 1))
            continue
        fi
        
        # Error 4: Dockerfile issues
        if grep -q "Error response from daemon\|COPY failed\|RUN failed" /tmp/compose_attempt_$ATTEMPT.log; then
            echo "Issue detected: Dockerfile build error"
            ERROR_LINE=$(grep "Error response from daemon\|COPY failed\|RUN failed" /tmp/compose_attempt_$ATTEMPT.log | head -3)
            echo "Error details:"
            echo "$ERROR_LINE"
            echo
            docker compose down
            docker compose build --no-cache
            ATTEMPT=$((ATTEMPT + 1))
            continue
        fi
        
        # If we can't identify the issue, show more context
        echo "Could not auto-identify issue. Showing full log:"
        cat /tmp/compose_attempt_$ATTEMPT.log
        echo
        echo "Full log saved to: /tmp/compose_attempt_$ATTEMPT.log"
        echo
        
        # Ask for next action
        echo "Possible next steps:"
        echo "1. Check Docker daemon is running: docker ps"
        echo "2. Check disk space: df -h"
        echo "3. Manual rebuild: docker compose build --no-cache"
        echo "4. Review Dockerfile for issues"
        echo "5. Check Python syntax: python3 validate_syntax.py"
        echo
        
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

echo
echo "❌ Failed after $MAX_ATTEMPTS attempts"
echo "Please review logs and issues manually"
echo "Logs saved in /tmp/compose_attempt_*.log"
echo
exit 1
