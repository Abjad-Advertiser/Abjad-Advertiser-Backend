import os

from dotenv import load_dotenv

load_dotenv()
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="debug",
    )
