from app.utils.cuid import generate_cuid
import logging

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

def test_generate_cuid():
    """Test the generation of a single CUID.
    
    This function generates a CUID and asserts that its length is 16 characters
    and that it is of type string. It also logs the generated CUID for reference.
    """
    cuid = generate_cuid()
    assert len(cuid) == 16
    logger.info(f"Generated CUID: {cuid}")
    assert isinstance(cuid, str)

def test_generate_multiple_cuids():
    """Test the generation of multiple CUIDs and check for duplicates.
    
    This function generates 1000 CUIDs and asserts that all generated CUIDs are unique.
    It logs the number of unique CUIDs generated.
    """
    cuids = [generate_cuid() for _ in range(1000)]  # Increased sample size for better duplicate detection
    assert len(cuids) == 1000
    unique_cuids = set(cuids)
    assert len(unique_cuids) == 1000, f"Found {len(cuids) - len(unique_cuids)} duplicate CUIDs"
    logger.info(f"Generated {len(cuids)} unique CUIDs")

def test_compare_cuids():
    """Test that two generated CUIDs are unique.
    
    This function generates two CUIDs and asserts that they are both of length 16
    and that they are not equal to each other.
    """
    cuid = generate_cuid()
    cuid2 = generate_cuid()
    assert len(cuid) == 16
    assert len(cuid2) == 16
    assert cuid != cuid2
