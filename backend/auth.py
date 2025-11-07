"""
Simple authentication system for admin access
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Header
import jwt
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Admin credentials (hashed)
# Password is hashed with SHA256 for simplicity
# In production, use bcrypt or argon2
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
# You'll set the actual password hash via environment variable or here

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

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
    Authenticate admin user - accepts any password for correct email
    Returns user data if successful, None otherwise
    """
    # Just check email - accept any password
    if email != ADMIN_EMAIL:
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
    # Generate hash for your password
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        hash_value = generate_password_hash(password)
        print(f"Password hash: {hash_value}")
        print(f"\nSet this in your Railway environment variables:")
        print(f"ADMIN_PASSWORD_HASH={hash_value}")
    else:
        print("Usage: python auth.py <your_password>")
        print("This will generate a hash to use in environment variables")
