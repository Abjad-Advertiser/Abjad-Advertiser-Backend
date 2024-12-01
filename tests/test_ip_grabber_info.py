import logging
from unittest.mock import Mock, patch

import pytest
import requests

from app.utils.ip_info_grabber import IPInfoGrabber, IPInformation

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock responses for different API services
IP_API_MOCK_RESPONSE = {
    "status": "success",
    "countryCode": "US",
    "lat": 37.751,
    "lon": -97.822,
    "timezone": "America/Chicago",
    "city": "Mountain View",
    "inEU": False,
}

IPINFO_MOCK_RESPONSE = {
    "ip": "8.8.8.8",
    "country_code": "US",
    "latitude": "37.751",
    "longitude": "-97.822",
    "timezone": "America/Chicago",
    "city": "Mountain View",
    "loc": "37.751,-97.822",
}


@pytest.fixture
def ip_grabber():
    return IPInfoGrabber()


def test_get_ip_info_ip_api_success(ip_grabber):
    with patch("requests.get") as mock_get:
        logger.info("Testing IP API success scenario")
        mock_response = Mock()
        mock_response.json.return_value = IP_API_MOCK_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        logger.debug("Attempting to get IP info with mocked IP API response")
        result = ip_grabber.get_ip_info("8.8.8.8")
        logger.info(f"IP API Success Result: {result.__dict__}")
        assert isinstance(result, IPInformation)
        assert result.ip == "8.8.8.8"
        assert result.country == "US"
        assert result.latitude == 37.751
        assert result.longitude == -97.822
        assert result.timezone == "America/Chicago"
        assert result.is_eu is False
        assert result.city == "Mountain View"


def test_get_ip_info_ipinfo_success(ip_grabber):
    with patch("requests.get") as mock_get:
        logger.info("Testing IPInfo success scenario")

        def side_effect(*args, **kwargs):
            if "ip-api.com" in args[0]:
                raise requests.RequestException()
            mock_response = Mock()
            mock_response.json.return_value = IPINFO_MOCK_RESPONSE
            mock_response.raise_for_status.return_value = None
            return mock_response

        mock_get.side_effect = side_effect
        logger.debug("Attempting to get IP info with mocked IPInfo response")
        result = ip_grabber.get_ip_info("8.8.8.8")
        logger.info(f"IPInfo Success Result: {result.__dict__}")
        assert isinstance(result, IPInformation)
        assert result.ip == "8.8.8.8"
        assert result.country == "US"
        assert result.latitude == 37.751
        assert result.longitude == -97.822
        assert result.timezone == "America/Chicago"
        assert result.city == "Mountain View"


def test_get_ip_info_all_apis_fail(ip_grabber):
    with patch("requests.get") as mock_get:
        logger.info("Testing all APIs failing scenario")
        mock_get.side_effect = requests.RequestException("API Error")

        with pytest.raises(requests.RequestException) as exc_info:
            logger.debug("Attempting to get IP info with mocked failing APIs")
            ip_grabber.get_ip_info("8.8.8.8")

        error_msg = str(exc_info.value)
        logger.info(f"Caught expected exception: {error_msg}")
        assert "API Error" in error_msg


def test_get_ip_info_invalid_ip():
    ip_grabber = IPInfoGrabber()
    logger.info("Testing invalid IP address scenario")
    with pytest.raises(requests.RequestException) as exc_info:
        logger.debug("Attempting to get info for invalid IP")
        ip_grabber.get_ip_info("invalid.ip.address")
    logger.info(f"Caught expected exception: {exc_info.value}")


def test_get_ip_info_ipv6(ip_grabber):
    with patch("requests.get") as mock_get:
        logger.info("Testing IPv6 scenario")
        mock_response = Mock()
        mock_response.json.return_value = IP_API_MOCK_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        logger.debug("Attempting to get IP info with mocked IPv6 response")
        result = ip_grabber.get_ip_info("2001:4860:4860::8888")
        logger.info(f"IPv6 Result: {result.__dict__}")
        assert isinstance(result, IPInformation)
        assert result.ip == "2001:4860:4860::8888"


def test_get_ip_info_with_api_key():
    ip_grabber = IPInfoGrabber(api_key="test_key")
    logger.info(f"IP Grabber with API Key: {ip_grabber.api_key}")
    assert ip_grabber.api_key == "test_key"
