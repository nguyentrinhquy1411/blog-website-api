from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User
from ..schemas import UserCreate, UserUpdate
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from ..utils.security.password import get_password_hash

async def get_user(db: AsyncSession, user_id: UUID):
    result = await db.execute(
        select(User)
        .where(User.user_id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User)
        .where(User.email == email)
    )
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_user(db: AsyncSession, user: UserCreate):
    # Check if email or username already exists
    existing_user = await db.execute(
        select(User)
        .where(
            (User.email == user.email) | 
            (User.username == user.username)
        )
    )
    existing_user = existing_user.scalars().first()
    
    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(
    db: AsyncSession, 
    user_id: UUID, 
    user: UserUpdate
):
    db_user = await get_user(db, user_id)
    
    update_data = user.model_dump(exclude_unset=True)
    
    # Special handling for password update
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: UUID):
    db_user = await get_user(db, user_id)
    
    # Soft delete (recommended)
    db_user.is_active = False
    await db.commit()
    
    # Or hard delete:
    # await db.delete(db_user)
    # await db.commit()
    
    return {"status": "success", "message": "User deleted"}
