import logging

from app.utils.worker import get_worker_id

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)


def test_get_worker_id():
    """
    Test the get_worker_id function to ensure it returns a valid worker ID.

    This test checks that the worker ID is not None and logs the worker ID
    for verification purposes. It is essential to confirm that the worker ID
    can be retrieved successfully, as it may be used for tracking or
    identifying worker processes in the application.
    """
    worker_id = get_worker_id()
    assert worker_id is not None
    logger.info(f"Worker ID: {worker_id}")
