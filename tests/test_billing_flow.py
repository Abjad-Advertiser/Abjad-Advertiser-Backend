"""
This module contains tests for the billing management flow.

To run this test file individually, use:
    pytest tests/test_billing_flow.py

The test covers the complete flow of billing data management.
"""

import http.client
import logging

import pytest
import requests

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable logging for requests library
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

http.client.HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


@pytest.fixture
def client():
    logger.info("Creating requests session")
    return requests.Session()


@pytest.mark.integration
def test_billing_flow(client):
    """
    Test the complete flow of billing data management.

    This test covers:
    1. User login
    2. Creating billing data
    3. Getting billing data
    4. Updating billing data
    """
    # Test variables
    base_url = "http://localhost:8000"
    test_user = {"email": "test.user.19957b90@example.com", "password": "Test123!@#"}
    test_billing_data = {
        "billing_address": "123 Test Street, Test City, 12345",
        "tax_id": "TAX123456",
        "currency": "USD",
    }
    updated_billing_data = {
        "billing_address": "456 Updated Street, Updated City, 67890",
        "tax_id": "TAX789012",
        "currency": "EUR",
    }

    # Step 1: Login user
    logger.info("Logging in test user")
    login_response = client.post(
        f"{base_url}/api/v1/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert login_response.status_code == 204
    headers = {
        "user-agent": "abjad/1.0",
        "cookie": f"token-v1={login_response.cookies.get('token-v1')}",
    }

    # Step 2: Create billing data
    logger.info("Creating billing data")
    create_response = client.post(
        f"{base_url}/api/v1/billing/",
        json=test_billing_data,
        headers=headers,
        cookies=login_response.cookies,
    )
    assert create_response.status_code == 200
    created_billing = create_response.json()
    assert created_billing["billing_address"] == test_billing_data["billing_address"]
    assert created_billing["tax_id"] == test_billing_data["tax_id"]
    assert created_billing["currency"] == test_billing_data["currency"]

    # Step 3: Get billing data
    logger.info("Getting billing data")
    get_response = client.get(
        f"{base_url}/api/v1/billing/", headers=headers, cookies=login_response.cookies
    )
    logger.info(get_response.text)
    assert get_response.status_code == 200
    get_billing = get_response.json()
    assert get_billing["billing_address"] == test_billing_data["billing_address"]

    # Step 4: Update billing data
    logger.info("Updating billing data")
    update_response = client.put(
        f"{base_url}/api/v1/billing/",
        json=updated_billing_data,
        headers=headers,
        cookies=login_response.cookies,
    )
    assert update_response.status_code == 200
    updated_billing = update_response.json()
    assert updated_billing["billing_address"] == updated_billing_data["billing_address"]
    assert updated_billing["tax_id"] == updated_billing_data["tax_id"]
    assert updated_billing["currency"] == updated_billing_data["currency"]

    # Verify the update
    verify_response = client.get(
        f"{base_url}/api/v1/billing/", headers=headers, cookies=login_response.cookies
    )
    assert verify_response.status_code == 200
    verify_billing = verify_response.json()
    assert verify_billing["billing_address"] == updated_billing_data["billing_address"]
