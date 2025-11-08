"""
Authentication system for admin access with bcrypt password hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Header
import jwt
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Admin credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify admin token from Authorization header
    Expects: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        payload = verify_token(token)
        return payload
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

def authenticate_admin(email: str, password: str) -> Optional[dict]:
    """
    Authenticate admin user with bcrypt password verification
    Returns user data if successful, None otherwise
    """
    # Check email first
    if email != ADMIN_EMAIL:
        return None
    
    # Verify password hash exists
    if not ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=500,
            detail="Admin password not configured. Please set ADMIN_PASSWORD_HASH environment variable."
        )
    
    # Verify password
    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return None

    return {
        "email": email,
        "role": "admin"
    }

# Utility function to generate password hash (run once to set up)
def generate_password_hash(password: str) -> str:
    """Generate password hash for storing in environment variable"""
    return hash_password(password)

if __name__ == "__main__":
    # Generate bcrypt hash for your password
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        hash_value = generate_password_hash(password)
        print(f"Bcrypt password hash generated successfully!")
        print(f"\nADMIN_PASSWORD_HASH={hash_value}")
        print(f"\nSet this in your environment variables (.env file or Railway/Vercel):")
        print(f"  1. Copy the hash above")
        print(f"  2. Add to .env: ADMIN_PASSWORD_HASH=<paste-hash-here>")
        print(f"  3. Also set ADMIN_EMAIL if different from default")
    else:
        print("Usage: python -m backend.auth <your_password>")
        print("This will generate a bcrypt hash to use in environment variables")
        print("\nExample:")
        print("  python -m backend.auth MySecurePassword123!")
