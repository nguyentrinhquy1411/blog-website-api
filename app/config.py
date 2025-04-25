import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from typing import AsyncGenerator


load_dotenv()

async def get_redis() -> AsyncGenerator[Redis, None]:
    try:
        yield redis
    finally:
        await redis.close()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("MY_SECRET_KEY", "your_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Cloudinary settings
    CLOUD_NAME: str = os.getenv("CLOUD_NAME")
    API_KEY: str = os.getenv("API_KEY")
    API_SECRET: str = os.getenv("API_SECRET")

settings = Settings()