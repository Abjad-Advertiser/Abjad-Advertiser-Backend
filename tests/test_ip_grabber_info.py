# TODO: Add tests for ip_info_grabber.py
from app.utils.ip_info_grabber import IPInfoGrabber


def test_ip_info_grabber():
    ip_info_grabber = IPInfoGrabber()
    ip_info = ip_info_grabber.get_ip_info("8.8.8.8")
    assert ip_info.ip == "8.8.8.8"
