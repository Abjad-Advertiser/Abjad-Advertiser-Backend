"""
This module contains tests for the authentication functionality of the application.

To run this test file individually, use the following command:
    pytest tests/test_auth.py -m "integration"

To run all tests in the tests/ folder, use:
    pytest tests/

Note: This test is marked as an integration test and is skipped by default.
To run integration tests, use: pytest -m integration
"""

import logging
import uuid
from collections.abc import Generator

import pytest
import requests
from dotenv import load_dotenv

from app.models.users import UserType

load_dotenv()
# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)


@pytest.fixture
def client() -> Generator[requests.Session, None, None]:
    """Create a test client session that preserves cookies between requests."""
    with requests.Session() as session:
        yield session


@pytest.fixture
def test_user_data():
    """Create test user data with required fields."""
    uuid_str = str(uuid.uuid4()).replace("-", "")[:8]
    return {
        "email": f"test.user.{uuid_str}@example.com",
        "password": "Test123!@#",
        "username": f"testuser_{uuid_str}",
        "user_type": UserType.PUBLISHER.value,  # Using uppercase enum value
        "full_name": "Test User",
        "company_name": "Test Company",
    }


def test_auth_flow(client: requests.Session, test_user_data: dict):
    """
    Test the complete authentication flow including:
    - User registration
    - Email verification (simulated)
    - Login
    - Get current user
    - Update user profile
    - Logout

    Note: This is an integration test that requires a running server.
    To run this test specifically: pytest -m integration
    """
    base_url = "http://localhost:8000/api/v1"

    # Step 1: Register new user
    logger.info(f"Registering new user: {test_user_data['email']}")
    register_response = client.post(f"{base_url}/register", json=test_user_data)
    assert register_response.status_code == 201, f"Registration failed: {
        register_response.text}"
    user_id = register_response.json()["id"]
    assert register_response.json()["email"] == test_user_data["email"]

    # Step 1.5: Verify email
    logger.info(f"Verifying email for user: {test_user_data['email']}")
    verify_response = client.post(
        f"{base_url}/verify", json={"token": "test_verification_token"}
    )
    assert verify_response.status_code == 400, f"Email verification failed: {
        verify_response.text}"

    # Step 1.6: Check user is verified
    me_response = client.get(f"{base_url}/users/me")
    assert (
        me_response.status_code == 401
    ), "Unverified user should not be able to access protected endpoints"

    # Step 1.7: Request verification token again
    request_verify_response = client.post(
        f"{base_url}/request-verify-token", json={"email": test_user_data["email"]}
    )
    assert (
        request_verify_response.status_code == 202
    ), "Failed to request new verification token"
    logger.info(f"Verification token {request_verify_response.cookies}")
    logger.info(f"Verification token {request_verify_response.content}")
    # Step 1.8: Verify with invalid token
    invalid_verify_response = client.post(
        f"{base_url}/verify", json={"token": "invalid_token"}
    )
    assert (
        invalid_verify_response.status_code == 400
    ), "Invalid token should be rejected"

    # Step 1.9: Verify with valid token
    verify_response = client.post(
        f"{base_url}/verify",
        json={"user_id": user_id, "token": "test_verification_token"},
    )
    assert verify_response.status_code == 200, f"Email verification failed: {
        verify_response.text}"

    # Step 2: Login
    logger.info(f"Logging in user: {test_user_data['email']}")
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post(
        f"{base_url}/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    logger.info("Login response status code: %s", login_response.status_code)
    logger.info("Login response content: %s", login_response.content)
    assert login_response.status_code == 204, "Login failed"
    # Verify that session cookie is set
    assert any(cookie.name == "session" for cookie in client.cookies)

    # Step 3: Get current user
    logger.info("Fetching current user profile")
    me_response = client.get(f"{base_url}/users/me")
    assert me_response.status_code == 200, "Failed to get current user"
    assert me_response.json()["email"] == test_user_data["email"]
    assert me_response.json()["username"] == test_user_data["username"]

    # Step 4: Update user profile
    logger.info("Updating user profile")
    update_data = {"full_name": "Updated Test User", "company_name": "Updated Company"}
    update_response = client.patch(f"{base_url}/users/me", json=update_data)
    assert update_response.status_code == 200, "Profile update failed"
    assert update_response.json()["full_name"] == update_data["full_name"]
    assert update_response.json()["company_name"] == update_data["company_name"]

    # Step 5: Logout
    logger.info("Logging out user")
    logout_response = client.post(f"{base_url}/logout")
    assert logout_response.status_code == 204, "Logout failed"

    # Verify logout by trying to access protected endpoint
    me_response = client.get(f"{base_url}/users/me")
    assert me_response.status_code == 401, "User still authenticated after logout"
