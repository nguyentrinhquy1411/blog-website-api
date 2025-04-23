# app/utils/security/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Tạo hash từ password (dùng cho đăng ký/user creation)"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra password có khớp với hash (dùng cho đăng nhập)"""
    return pwd_context.verify(plain_password, hashed_password)