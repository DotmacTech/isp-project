#!/bin/bash

# Test Runner Script for ISP Billing System
# This script runs comprehensive tests for both frontend and backend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main test function
run_tests() {
    local test_type=${1:-"all"}
    
    print_status "Starting ISP Billing System test suite..."
    print_status "Test type: $test_type"
    
    case $test_type in
        "backend"|"be")
            run_backend_tests
            ;;
        "frontend"|"fe")
            run_frontend_tests
            ;;
        "integration"|"int")
            run_integration_tests
            ;;
        "performance"|"perf")
            run_performance_tests
            ;;
        "security"|"sec")
            run_security_tests
            ;;
        "all")
            run_backend_tests
            run_frontend_tests
            run_integration_tests
            print_success "All test suites completed successfully!"
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_status "Available options: backend|be, frontend|fe, integration|int, performance|perf, security|sec, all"
            exit 1
            ;;
    esac
}

# Backend tests
run_backend_tests() {
    print_status "Running backend tests..."
    
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found!"
        exit 1
    fi
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        if [ -d "venv" ]; then
            source venv/bin/activate
        else
            source .venv/bin/activate
        fi
    fi
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock bandit safety
    
    # Run linting
    print_status "Running code quality checks..."
    python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || print_warning "Linting issues found"
    
    # Run security checks
    print_status "Running security scan..."
    bandit -r . -x tests/ -ll || print_warning "Security issues found"
    
    # Run tests
    print_status "Running unit tests..."
    pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
    
    cd ..
    print_success "Backend tests completed!"
}

# Frontend tests
run_frontend_tests() {
    print_status "Running frontend tests..."
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found!"
        exit 1
    fi
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "Node modules not found. Installing..."
        npm install
    fi
    
    # Run linting
    print_status "Running ESLint..."
    npm run lint || print_warning "Linting issues found"
    
    # Run tests
    print_status "Running Jest tests..."
    npm run test:ci
    
    # Build check
    print_status "Testing build process..."
    npm run build
    
    # Storybook build check
    print_status "Testing Storybook build..."
    npm run build-storybook
    
    cd ..
    print_success "Frontend tests completed!"
}

# Integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    # Start services if needed
    print_status "Checking if services are running..."
    
    # Check if backend is running
    if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_warning "Backend not running. Starting backend..."
        cd backend
        source venv/bin/activate 2>/dev/null || source .venv/bin/activate
        uvicorn main:app --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        sleep 5
        cd ..
    fi
    
    # Run integration tests
    cd backend
    source venv/bin/activate 2>/dev/null || source .venv/bin/activate
    pytest tests/integration/ -v
    cd ..
    
    # Clean up
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend service..."
        kill $BACKEND_PID
    fi
    
    print_success "Integration tests completed!"
}

# Performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    cd backend
    source venv/bin/activate 2>/dev/null || source .venv/bin/activate
    
    # Install locust if not present
    pip install locust
    
    # Check if backend is running
    if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_warning "Backend not running. Starting backend..."
        uvicorn main:app --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        sleep 5
    fi
    
    # Run performance tests
    print_status "Running Locust performance tests..."
    locust --host=http://localhost:8000 --users 5 --spawn-rate 1 --run-time 30s --headless
    
    # Clean up
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    
    cd ..
    print_success "Performance tests completed!"
}

# Security tests
run_security_tests() {
    print_status "Running security tests..."
    
    # Backend security
    cd backend
    source venv/bin/activate 2>/dev/null || source .venv/bin/activate
    
    print_status "Running Bandit security scan..."
    bandit -r . -x tests/ -f json -o bandit-report.json
    
    print_status "Running Safety check..."
    safety check --file requirements.txt
    
    cd ../frontend
    
    print_status "Running npm audit..."
    npm audit --audit-level moderate
    
    cd ..
    print_success "Security tests completed!"
}

# Help function
show_help() {
    echo "ISP Billing System Test Runner"
    echo ""
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test types:"
    echo "  backend, be      - Run backend tests only"
    echo "  frontend, fe     - Run frontend tests only"
    echo "  integration, int - Run integration tests"
    echo "  performance, perf- Run performance tests"
    echo "  security, sec    - Run security tests"
    echo "  all              - Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  $0                # Run all tests"
    echo "  $0 backend        # Run only backend tests"
    echo "  $0 fe            # Run only frontend tests"
    echo "  $0 integration   # Run only integration tests"
}

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Check dependencies
print_status "Checking dependencies..."

if ! command_exists python; then
    print_error "Python is not installed!"
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed!"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed!"
    exit 1
fi

# Run tests
run_tests "$1"

print_success "Test runner completed successfully!"