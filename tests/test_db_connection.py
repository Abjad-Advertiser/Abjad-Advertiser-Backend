import pytest

from app.db import database_health_check


@pytest.mark.asyncio
async def test_database_connection():
    """
    Test database connectivity using SQLAlchemy asynchronously.
    """
    try:
        result = await database_health_check()
        assert result["reachable"] is True
    except Exception as e:
        pytest.fail(f"Database connection test failed: {str(e)}")
