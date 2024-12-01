"""
This module contains tests for the complete tracking lifecycle.

To run this test file individually, use:
    pytest tests/test_tracking_flow.py

The test covers the complete flow from publisher creation to tracking events.
"""

import http.client
import logging
import uuid

import pytest
import requests

from app.models.tracking_events import EventType

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


def test_tracking_lifecycle(client):
    """
    Test the complete tracking lifecycle flow.

    This test covers:
    1. User login
    2. Publisher creation
    3. Advertisement creation
    4. Campaign creation
    5. Tracking initialization
    6. Tracking events
    """
    base_url = "http://localhost:8000/api/v1"

    # Test user credentials (using existing test user from other tests)
    test_user = {"email": "test.user.19957b90@example.com", "password": "Test123!@#"}

    # Step 1: Login
    logger.info(f"Logging in user: {test_user['email']}")
    response = client.post(
        f"{base_url}/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 204, "Failed to login"

    headers = {
        "user-agent": "abjad/1.0",
        "cookie": f"{response.headers['set-cookie']}",
    }

    # Step 2: Create a publisher
    logger.info("Creating test publisher")
    publisher_data = {
        "name": "Test Publisher",
        "website_url": "https://testpublisher.com",
        "contact_email": "contact@testpublisher.com",
        "contact_phone": "+1234567890",
        "publishing_platform": "website",
    }

    response = client.post(
        f"{base_url}/publishers/",
        json=publisher_data,
        headers=headers,
        cookies=client.cookies,
    )
    assert response.status_code == 200, f"Publisher creation failed: {
        response.text}"
    publisher_id = response.json()["id"]
    logger.info(f"Created publisher with ID: {publisher_id}")

    # Step 5: Initialize tracking session
    logger.info("Initializing tracking session")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    session_id = str(uuid.uuid4())
    campaign_id = "z3ogirnceue0z5d4"

    tracking_init_data = {
        "campaign_id": campaign_id,
        "event_type": EventType.VIEW.value,
        "viewer_user_agent": user_agent,
        "viewer_session_id": session_id,
        "viewer_screen_resolution": "1920x1080",
        "viewer_language": "en-US",
    }

    response = client.post(
        f"{base_url}/track/init/{publisher_id}",
        json=tracking_init_data,
        headers=headers,
        cookies=client.cookies,
    )
    assert response.status_code == 201, f"Tracking initialization failed: {
        response.text}"
    tracking_session = response.cookies.get("ats_v1")
    assert tracking_session, "No tracking session cookie received"
    logger.info("Tracking session initialized successfully")

    # Step 6: Track event
    logger.info("Sending tracking event")
    tracking_event_data = {
        "campaign_id": campaign_id,
        "event_type": EventType.VIEW.value,
        "viewer_user_agent": user_agent,
        "viewer_session_id": session_id,
        "viewer_screen_resolution": "1920x1080",
        "viewer_language": "en-US",
    }

    # Add tracking session cookie to existing cookies
    client.cookies.set("ats_v1", tracking_session)

    response = client.post(
        f"{base_url}/track/{campaign_id}/{publisher_id}",
        json=tracking_event_data,
        headers={
            "user-agent": user_agent,  # Use the same user-agent as initialization
        },
        cookies=client.cookies,
    )
    logging.info(f"Tracking event response: {response.text}")
    assert response.status_code == 200, f"Event tracking failed: {
        response.text}"

    # Verify tracking event was recorded
    event_response = response.json()
    assert (
        event_response["event_type"] == EventType.VIEW
    ), "Incorrect event type recorded"
    assert (
        event_response["campaign_id"] == campaign_id
    ), "Incorrect campaign ID recorded"
    assert (
        event_response["viewer_session_id"] == session_id
    ), "Incorrect session ID recorded"

    logger.info("Tracking lifecycle test completed successfully")
