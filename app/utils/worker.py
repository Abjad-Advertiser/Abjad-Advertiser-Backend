import random
import socket

def get_worker_id() -> int:
    """
    Generate a unique worker ID between 0-31 for Snowflake ID generation.
    
    This function attempts to create a deterministic worker ID based on the machine's 
    hostname. If that fails, it falls back to generating a random ID.
    
    The worker ID is used by the Snowflake algorithm to ensure unique IDs across
    different server instances.

    Returns:
        int: A worker ID between 0 and 31 inclusive
    
    Note:
        The worker ID range of 0-31 is a limitation of the Snowflake algorithm,
        which uses 5 bits for the worker ID component.
    """
    try:
        hostname = socket.gethostname()
        worker_id = int(hash(hostname) % 32)
    except Exception:
        # Fallback to random ID if hostname lookup fails
        worker_id = random.randint(0, 31)
    return worker_id