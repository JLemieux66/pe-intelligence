"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.schemas.requests import LoginRequest, LoginResponse
from backend.auth import authenticate_admin, create_access_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Login endpoint for admin authentication
    Returns JWT token on successful login
    """
    user = authenticate_admin(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        email=user["email"]
    )
