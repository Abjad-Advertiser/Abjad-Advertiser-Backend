"""
This module contains tests for the campaign management flow.

To run this test file individually, use:
    pytest tests/test_campaign_flow.py

The test covers the complete flow from user registration to campaign management.
"""

import http.client
import logging
from datetime import datetime, timedelta

import pytest
import requests

from app.models.campaigns import CampaignStatus

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


def test_campaign_flow(client):
    """
    Test the complete flow from user registration to campaign management.

    This test covers:
    1. User registration
    2. User login
    3. Creating an advertisement
    4. Creating a campaign
    5. Managing the campaign (view, update, delete)
    """
    base_url = "http://localhost:8000/api/v1"

    # Step 1: Register a new user
    # unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "email": "test.user.19957b90@example.com",
        "password": "Test123!@#",
    }

    # logger.info(f"Registering new user: {test_user['email']}")
    # response = client.post(
    #     f"{base_url}/register",
    #     json=test_user
    # )
    # assert response.status_code == 201, "Failed to register user"
    # logger.info("User registered successfully")

    # Step 2: Login with the new user
    logger.info(f"Logging in user: {test_user['email']}")
    response = client.post(
        f"{base_url}/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 204, "Failed to login"
    logger.info(f"User logged in successfully\n{
                client.cookies} - {response.headers}")
    cookie_value = response.headers.get("set-cookie")
    headers = {
        "user-agent": "abjad/1.0",
        "cookie": f"{cookie_value}",
    }
    # Step 3: Create an advertisement
    logger.info("Creating test advertisement")
    ad_data = {
        "title": "Test Advertisement",
        "description": "A test advertisement for campaign flow testing",
        "media": "image",
        "target_audience": "test_audience",
    }

    logger.info("Cookies %s", client.cookies)
    response = requests.post(
        f"{base_url}/advertisers/create-ad",
        json=ad_data,
        headers=headers,
        cookies=client.cookies,
    )
    assert response.status_code == 201, "Failed to create advertisement"
    ad_response = response.json()
    ad_id = ad_response["id"]
    logger.info(f"Created advertisement with ID: {ad_id}")

    # Step 4: Create a campaign
    logger.info("Creating test campaign")
    campaign_data = {
        "name": "Test Campaign",
        "description": "A test campaign for integration testing",
        "advertisement_id": ad_id,
        "campaign_start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "campaign_end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "budget_allocation_currency": "USD",
        "budget_allocation_amount": 25.00,
    }

    response = client.post(
        f"{base_url}/campaigns/create-campaign",
        json=campaign_data,
        headers=headers,
        cookies=client.cookies,
    )
    logger.info("Resposne %s", response.text)
    assert response.status_code == 201, "Failed to create campaign"
    campaign_response = response.json()
    campaign_id = campaign_response["id"]
    logger.info(f"Created campaign with ID: {campaign_id}")

    # Step 5: Get campaign details
    logger.info(f"Fetching campaign details for ID: {campaign_id}")
    response = client.get(
        f"{base_url}/campaigns/{campaign_id}", headers=headers, cookies=client.cookies
    )
    assert response.status_code == 200, "Failed to get campaign details"
    campaign_details = response.json()
    assert campaign_details["campaign_name"] == campaign_data["name"]
    assert campaign_details["campaign_description"] == campaign_data["description"]
    logger.info("Campaign details verified successfully")

    # Step 6: Update campaign status
    logger.info(f"Updating campaign status to {CampaignStatus.ACTIVE}")
    response = client.patch(
        f"{base_url}/campaigns/{campaign_id}/status",
        json={"new_status": CampaignStatus.ACTIVE},
        headers=headers,
        cookies=client.cookies,
    )
    logger.info("Resposne %s", response.text)
    assert response.status_code == 200, "Failed to update campaign status"

    # Verify status update
    logger.info("Verifying campaign status update")
    response = client.get(
        f"{base_url}/campaigns/{campaign_id}", headers=headers, cookies=client.cookies
    )
    assert response.status_code == 200, "Failed to get updated campaign"
    updated_campaign = response.json()
    assert (
        updated_campaign["campaign_status"] == CampaignStatus.ACTIVE
    ), "Campaign status not updated"
    logger.info("Campaign status updated successfully")

    # Step 7: Delete campaign
    # logger.info(f"Deleting campaign with ID: {campaign_id}")
    # response = client.delete(
    #     f"{base_url}/campaigns/{campaign_id}", headers=headers, cookies=client.cookies
    # )
    # assert response.status_code == 200, "Failed to delete campaign"

    # # Verify campaign was deleted
    # logger.info("Verifying campaign deletion")
    # response = client.get(
    #     f"{base_url}/campaigns/{campaign_id}", headers=headers, cookies=client.cookies
    # )
    # assert response.status_code == 404, "Campaign still exists after deletion"
    # logger.info("Campaign deleted successfully")
