#!/bin/bash

# Load Testing Runner for DeskMate
# Provides different load testing scenarios and configurations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if required tools are installed
check_dependencies() {
    print_info "Checking dependencies..."

    if ! command -v locust &> /dev/null; then
        print_error "Locust is not installed. Install with: pip install locust"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    print_success "All dependencies are available"
}

# Check if DeskMate services are running
check_services() {
    print_info "Checking DeskMate services..."

    # Check backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend service is running (port 8000)"
    else
        print_warning "Backend service is not responding on port 8000"
        print_info "Start with: docker-compose up -d"
        return 1
    fi

    # Check frontend (optional)
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend service is running (port 3000)"
    else
        print_warning "Frontend service is not responding on port 3000"
    fi

    return 0
}

# Install Python dependencies for load testing
install_dependencies() {
    print_info "Installing load testing dependencies..."

    python3 -m pip install locust websocket-client psutil

    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Run basic load test
run_basic_test() {
    print_header "Running Basic Load Test"
    print_info "Test configuration: 10 users, 2/sec spawn rate, 60 seconds"

    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=10 \
        --spawn-rate=2 \
        --run-time=60s \
        --headless \
        --html=results/basic_test_report.html \
        --csv=results/basic_test

    print_success "Basic load test completed. Results in results/basic_test_report.html"
}

# Run stress test
run_stress_test() {
    print_header "Running Stress Test"
    print_info "Test configuration: 50 users, 5/sec spawn rate, 300 seconds"

    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=50 \
        --spawn-rate=5 \
        --run-time=300s \
        --headless \
        --html=results/stress_test_report.html \
        --csv=results/stress_test

    print_success "Stress test completed. Results in results/stress_test_report.html"
}

# Run WebSocket focused test
run_websocket_test() {
    print_header "Running WebSocket Load Test"
    print_info "Test configuration: WebSocket users only, 20 users, 2/sec spawn rate, 120 seconds"

    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=20 \
        --spawn-rate=2 \
        --run-time=120s \
        --headless \
        --html=results/websocket_test_report.html \
        --csv=results/websocket_test \
        DeskMateWebSocketUser

    print_success "WebSocket test completed. Results in results/websocket_test_report.html"
}

# Run Brain Council focused test
run_brain_council_test() {
    print_header "Running Brain Council Load Test"
    print_info "Test configuration: Heavy Brain Council usage, 15 users, 1/sec spawn rate, 180 seconds"

    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=15 \
        --spawn-rate=1 \
        --run-time=180s \
        --headless \
        --html=results/brain_council_test_report.html \
        --csv=results/brain_council_test \
        HeavyLoadUser

    print_success "Brain Council test completed. Results in results/brain_council_test_report.html"
}

# Run performance benchmark
run_performance_benchmark() {
    print_header "Running Performance Benchmark"
    print_info "Comprehensive performance test across all endpoints"

    # Create results directory
    mkdir -p results

    # Sequential test phases
    print_info "Phase 1: Light load (simulating normal usage)"
    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=5 \
        --spawn-rate=1 \
        --run-time=60s \
        --headless \
        --csv=results/benchmark_light \
        LightLoadUser

    print_info "Phase 2: Medium load (moderate usage)"
    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=25 \
        --spawn-rate=3 \
        --run-time=120s \
        --headless \
        --csv=results/benchmark_medium \
        DeskMateAPIUser

    print_info "Phase 3: Heavy load (peak usage)"
    locust -f locustfile.py \
        --host=http://localhost:8000 \
        --users=50 \
        --spawn-rate=5 \
        --run-time=180s \
        --headless \
        --html=results/benchmark_heavy_report.html \
        --csv=results/benchmark_heavy

    print_success "Performance benchmark completed. Check results/ directory for detailed reports"
}

# Run interactive test (with web UI)
run_interactive_test() {
    print_header "Starting Interactive Load Test"
    print_info "Web UI will be available at http://localhost:8089"
    print_info "Configure users and test parameters in the web interface"
    print_info "Press Ctrl+C to stop the test"

    locust -f locustfile.py --host=http://localhost:8000
}

# Generate summary report
generate_summary() {
    print_header "Load Test Summary Report"

    if [ -d "results" ]; then
        print_info "Test Results Summary:"
        echo ""

        for file in results/*.html; do
            if [ -f "$file" ]; then
                echo -e "${CYAN}📊 $(basename "$file")${NC}"
            fi
        done

        echo ""
        print_info "CSV data files:"
        for file in results/*.csv; do
            if [ -f "$file" ]; then
                echo -e "${YELLOW}📈 $(basename "$file")${NC}"
            fi
        done

        echo ""
        print_info "Open HTML reports in your browser for detailed analysis"
    else
        print_warning "No results directory found. Run some tests first."
    fi
}

# Clean up old results
clean_results() {
    print_info "Cleaning up old test results..."

    if [ -d "results" ]; then
        rm -rf results/*
        print_success "Results directory cleaned"
    else
        print_info "No results directory to clean"
    fi
}

# Main menu
show_menu() {
    print_header "DeskMate Load Testing Suite"
    echo ""
    echo -e "${CYAN}Available test scenarios:${NC}"
    echo "1. Basic Load Test (10 users, 60s)"
    echo "2. Stress Test (50 users, 300s)"
    echo "3. WebSocket Test (20 users, 120s)"
    echo "4. Brain Council Test (15 users, 180s)"
    echo "5. Performance Benchmark (comprehensive)"
    echo "6. Interactive Test (web UI)"
    echo ""
    echo -e "${CYAN}Utility options:${NC}"
    echo "7. Install Dependencies"
    echo "8. Check Services"
    echo "9. Generate Summary Report"
    echo "10. Clean Results"
    echo "11. Exit"
    echo ""
}

# Parse command line arguments
case "$1" in
    "basic")
        check_services && run_basic_test
        ;;
    "stress")
        check_services && run_stress_test
        ;;
    "websocket")
        check_services && run_websocket_test
        ;;
    "brain")
        check_services && run_brain_council_test
        ;;
    "benchmark")
        check_services && run_performance_benchmark
        ;;
    "interactive")
        check_services && run_interactive_test
        ;;
    "install")
        install_dependencies
        ;;
    "check")
        check_dependencies && check_services
        ;;
    "summary")
        generate_summary
        ;;
    "clean")
        clean_results
        ;;
    *)
        # Interactive menu
        check_dependencies

        while true; do
            show_menu
            read -p "Choose an option (1-11): " choice

            case $choice in
                1)
                    mkdir -p results
                    check_services && run_basic_test
                    ;;
                2)
                    mkdir -p results
                    check_services && run_stress_test
                    ;;
                3)
                    mkdir -p results
                    check_services && run_websocket_test
                    ;;
                4)
                    mkdir -p results
                    check_services && run_brain_council_test
                    ;;
                5)
                    mkdir -p results
                    check_services && run_performance_benchmark
                    ;;
                6)
                    check_services && run_interactive_test
                    ;;
                7)
                    install_dependencies
                    ;;
                8)
                    check_services
                    ;;
                9)
                    generate_summary
                    ;;
                10)
                    clean_results
                    ;;
                11)
                    print_info "Exiting load testing suite"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option. Please choose 1-11."
                    ;;
            esac

            echo ""
            read -p "Press Enter to continue..."
        done
        ;;
esac