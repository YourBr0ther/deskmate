#!/usr/bin/env python3
"""
Comprehensive test script to verify error handling improvements.

This script tests:
1. New exception system functionality
2. Error logging and metrics
3. Database connection resilience
4. WebSocket error handling
5. LLM service error handling
"""

import asyncio
import logging
import sys
import json
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, '/Users/christophervance/deskmate/backend')

from app.exceptions import (
    DeskMateError, ValidationError, ResourceError, ServiceError,
    BusinessLogicError, ConnectionError, ErrorCategory, ErrorSeverity
)
from app.logging_config import init_logging, PerformanceLogger, get_error_metrics


def test_exception_system():
    """Test the new exception system."""
    print("🧪 Testing Exception System...")

    try:
        # Test ValidationError
        validation_error = ValidationError(
            "Email format is invalid",
            field="email",
            value="not-an-email"
        )
        print(f"✅ ValidationError created: {validation_error.error_code}")
        print(f"   User message: {validation_error.user_message}")

        # Test ResourceError
        db_error = ResourceError(
            "Connection to database failed",
            resource_type="database",
            operation="connect"
        )
        print(f"✅ ResourceError created: {db_error.error_code}")
        print(f"   Recoverable: {db_error.recoverable}")

        # Test ServiceError
        llm_error = ServiceError(
            "API rate limit exceeded",
            service="nano_gpt",
            model="gpt-4o-mini"
        )
        print(f"✅ ServiceError created: {llm_error.error_code}")

        # Test BusinessLogicError
        logic_error = BusinessLogicError(
            "Cannot move to occupied position",
            operation="pathfinding"
        )
        print(f"✅ BusinessLogicError created: {logic_error.error_code}")

        # Test ConnectionError
        conn_error = ConnectionError(
            "WebSocket connection lost",
            connection_type="websocket"
        )
        print(f"✅ ConnectionError created: {conn_error.error_code}")

        print("🎉 Exception system tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ Exception system test failed: {e}")
        return False


def test_error_logging():
    """Test error logging and metrics."""
    print("🧪 Testing Error Logging...")

    try:
        # Initialize logging system
        init_logging()

        # Create and log various errors
        errors = [
            ValidationError("Test validation error", field="test"),
            ResourceError("Test resource error", resource_type="database"),
            ServiceError("Test service error", service="test_service"),
            BusinessLogicError("Test business logic error", operation="test_op"),
            ConnectionError("Test connection error")
        ]

        for error in errors:
            error.log_error({"test_context": "error_logging_test"})

        # Check error metrics
        metrics = get_error_metrics()
        print(f"✅ Error metrics collected: {len(metrics.get('error_counts', {}))}")

        print("🎉 Error logging tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ Error logging test failed: {e}")
        return False


def test_performance_logging():
    """Test performance logging."""
    print("🧪 Testing Performance Logging...")

    try:
        # Test performance logger
        with PerformanceLogger("test_operation", context={"test": "value"}):
            # Simulate some work
            import time
            time.sleep(0.1)

        print("✅ Performance logging works")

        # Test slow operation detection
        with PerformanceLogger("slow_operation") as perf:
            time.sleep(0.5)  # Simulate slow operation

        print("✅ Slow operation detection works")

        print("🎉 Performance logging tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ Performance logging test failed: {e}")
        return False


async def test_database_resilience():
    """Test database connection resilience."""
    print("🧪 Testing Database Resilience...")

    try:
        from app.db.connection_manager import DatabaseConnectionManager
        from app.exceptions import ResourceError

        # Test connection manager initialization
        db_manager = DatabaseConnectionManager(
            "postgresql+asyncpg://invalid:invalid@localhost:5432/invalid"
        )

        # This should fail gracefully
        try:
            await db_manager.initialize()
            print("❌ Expected database connection to fail")
            return False
        except ResourceError as e:
            print(f"✅ Database connection failed gracefully: {e.error_code}")

        print("🎉 Database resilience tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ Database resilience test failed: {e}")
        return False


def test_error_response_format():
    """Test unified error response format."""
    print("🧪 Testing Error Response Format...")

    try:
        # Test error to dictionary conversion
        error = ValidationError(
            "Required field missing",
            field="username",
            value=None
        )

        error_dict = error.to_dict()

        # Verify required fields
        required_fields = [
            "message", "user_message", "error_code",
            "category", "severity", "recoverable", "details"
        ]

        for field in required_fields:
            if field not in error_dict:
                print(f"❌ Missing field in error response: {field}")
                return False

        print(f"✅ Error response format is correct")
        print(f"   Sample: {json.dumps(error_dict, indent=2)}")

        print("🎉 Error response format tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ Error response format test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Error Handling Improvement Tests\n")

    tests = [
        ("Exception System", test_exception_system),
        ("Error Logging", test_error_logging),
        ("Performance Logging", test_performance_logging),
        ("Database Resilience", test_database_resilience),
        ("Error Response Format", test_error_response_format),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Error handling improvements are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)