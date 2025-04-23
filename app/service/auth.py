from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.security.password import verify_password
from .user import get_user_by_email
from fastapi import HTTPException, status


async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
):
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please check email or password!"
        )
    elif not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not found user, please sign up!"
        )
    return user
