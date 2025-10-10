#!/bin/bash

# Docker Sandbox Fix Verification Test Runner
# This script runs all tests to verify the Docker sandbox fixes

set -e

echo "🚀 Starting Docker Sandbox Fix Verification Tests"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ ${message}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ ${message}${NC}"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "sandbox/sandbox.py" ]; then
    print_status "ERROR" "Please run this script from the backend directory"
    exit 1
fi

print_status "INFO" "Current directory: $(pwd)"
print_status "INFO" "Python version: $(python3 --version)"

# Check if required files exist
required_files=(
    "sandbox/sandbox.py"
    "sandbox/docker_sandbox.py"
    "test_sandbox_fix.py"
    "test_sandbox_unit.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_status "ERROR" "Required file not found: $file"
        exit 1
    fi
done

print_status "SUCCESS" "All required files found"

# Run unit tests first
echo ""
print_status "INFO" "Running Unit Tests..."
echo "=================================="

if python3 test_sandbox_unit.py; then
    print_status "SUCCESS" "Unit tests passed"
else
    print_status "ERROR" "Unit tests failed"
    exit 1
fi

# Run comprehensive tests
echo ""
print_status "INFO" "Running Comprehensive Tests..."
echo "=========================================="

if python3 test_sandbox_fix.py; then
    print_status "SUCCESS" "Comprehensive tests passed"
else
    print_status "ERROR" "Comprehensive tests failed"
    exit 1
fi

# Summary
echo ""
echo "=================================================="
print_status "SUCCESS" "ALL TESTS PASSED!"
print_status "SUCCESS" "Docker sandbox fix verification completed successfully"
echo "=================================================="

print_status "INFO" "The following issues have been resolved:"
echo "  • Session creation race conditions"
echo "  • 'Session supervisord-session not found' errors"
echo "  • Missing session verification"
echo "  • Lack of retry mechanism"
echo "  • Type compatibility issues"

print_status "INFO" "The Docker sandbox should now work reliably without timing issues."

exit 0
