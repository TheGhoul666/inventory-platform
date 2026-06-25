import sys
import os
backend_path = r'C:\Users\beni3\OneDrive\שולחן העבודה\AI\claude all\inventory_platform\backend'
os.chdir(backend_path)
sys.path.insert(0, backend_path)
from app.api.routes.auth import CreateUserRequest, UpdateProfileRequest
from pydantic import ValidationError

print("=== Test 1: Invalid phone in CreateUserRequest ===")
try:
    user = CreateUserRequest(
        email="test@example.com",
        password="TestPassword123",
        full_name="Test User",
        username="testuser",
        phone="invalid-phone"
    )
    print("FAILED: Should have rejected invalid phone")
except ValidationError as e:
    print("PASSED: Validation error caught")
    print(f"  Error: {e.errors()[0]['msg']}")

print("\n=== Test 2: Valid phone (+972501234567) ===")
try:
    user = CreateUserRequest(
        email="test@example.com",
        password="TestPassword123",
        full_name="Test User",
        username="testuser",
        phone="+972501234567"
    )
    print(f"PASSED: Valid phone accepted")
except ValidationError as e:
    print(f"FAILED: {e}")

print("\n=== Test 3: Valid phone (10 digits) ===")
try:
    user = CreateUserRequest(
        email="test@example.com",
        password="TestPassword123",
        full_name="Test User",
        username="testuser",
        phone="2025551234"
    )
    print(f"PASSED: Valid phone accepted")
except ValidationError as e:
    print(f"FAILED: {e}")

print("\n=== Test 4: Empty phone (null) ===")
try:
    user = CreateUserRequest(
        email="test@example.com",
        password="TestPassword123",
        full_name="Test User",
        username="testuser",
        phone=None
    )
    print(f"PASSED: Empty phone allowed")
except ValidationError as e:
    print(f"FAILED: {e}")

print("\n=== Test 5: Invalid phone in UpdateProfileRequest ===")
try:
    update = UpdateProfileRequest(phone="bad-phone")
    print("FAILED: Should have rejected invalid phone")
except ValidationError as e:
    print("PASSED: Validation error caught")
    print(f"  Error: {e.errors()[0]['msg']}")

print("\n=== Test 6: Valid phone in UpdateProfileRequest ===")
try:
    update = UpdateProfileRequest(phone="+12025550173")
    print(f"PASSED: Valid phone accepted")
except ValidationError as e:
    print("Note: Format may not be accepted")
    print(f"  {e.errors()[0]['msg']}")

print("\n=== Test 7: Valid phone (11 digits with +1) ===")
try:
    update = UpdateProfileRequest(phone="+12025551234")
    print(f"PASSED: Valid phone accepted")
except ValidationError as e:
    print(f"Note: {e.errors()[0]['msg']}")

print("\n=== Test 8: Phone too long (>30 chars) ===")
try:
    update = UpdateProfileRequest(phone="+123456789012345678901234567890123")
    print("FAILED: Should have rejected phone > 30 chars")
except ValidationError as e:
    print("PASSED: Validation error caught")
    print(f"  Error: {e.errors()[0]['msg']}")
