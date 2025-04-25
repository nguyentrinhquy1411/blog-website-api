from fastapi import FastAPI
import os  # Add this import to check environment variables

from .database import init_db
from .routes import user_router, post_router, auth_router, test_router, category_router, tag_router, media_router, comment_router
from .middlewares.core import setup_cors
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from .config import settings  # Import settings

def create_app() -> FastAPI:
    """Factory function để tạo app (hữu ích khi testing)"""
    app = FastAPI(
        title="Blog API",
        description="API for blogging platform",
        version="1.0.0",
        docs_url="/docs"  # Có thể tắt bằng None nếu không cần
    )

    setup_cors(app)

    # Event handlers
    @app.on_event("startup")
    async def startup():
        # Debug environment variables
        print("Environment variables for Cloudinary:")
        print(f"CLOUD_NAME: '{os.getenv('CLOUD_NAME')}'")
        print(f"API_KEY: '{os.getenv('API_KEY')}'")
        print(f"API_SECRET: '{os.getenv('API_SECRET')}'")
        print(f"From settings - CLOUD_NAME: '{settings.CLOUD_NAME}'")
        print(f"From settings - API_KEY: '{settings.API_KEY}'")
        print(f"From settings - API_SECRET: '{settings.API_SECRET if settings.API_SECRET else 'Not set'}'")
        
        await init_db()
        # Có thể thêm các khởi tạo khác ở đây
        redis = aioredis.from_url("redis://redis:6379", encoding="utf-8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        # print("✅ Redis Cache initialized!")
        try:
            pong = await redis.ping()
            print(f"Redis connected: {pong}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")

    # Include routers với prefix
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(post_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(tag_router, prefix="/api/v1")
    app.include_router(category_router, prefix="/api/v1")
    app.include_router(test_router, prefix="/api/v1")
    app.include_router(media_router, prefix="/api/v1")
    app.include_router(comment_router, prefix="/api/v1")

    return app

# Khởi tạo app instance
app = create_app()