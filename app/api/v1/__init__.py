from fastapi import APIRouter

from app.db import database_health_check

general_router = APIRouter()


async def general_health_check():
    response = await database_health_check()
    return {"database": response}


@general_router.get("/health/check")
async def health_check_endpoint():
    response = await general_health_check()
    return response
