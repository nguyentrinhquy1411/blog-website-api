from fastapi import APIRouter
from fastapi_cache.decorator import cache

router = APIRouter()

@router.get("/test-cache")
@cache(expire=10)
async def test_cache():
    print("⚡ NOT FROM CACHE")
    return {"msg": "hello"}
