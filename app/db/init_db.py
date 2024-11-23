from app.models import create_db_and_tables_fastapi_users

async def init_db():
    await create_db_and_tables_fastapi_users()