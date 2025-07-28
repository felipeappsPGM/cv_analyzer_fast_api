# =============================================
# app/api/v1/endpoints/auth.py
# =============================================
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta

from app.config.database import get_db
from app.config.settings import get_settings
from app.services.user_service import UserService
from app.core.security import verify_password, create_access_token, verify_token
from app.core.exceptions import InvalidCredentialsError, UserNotFoundError
from app.schemas.auth import (
    LoginRequest, 
    TokenResponse, 
    UserClaims,
    RefreshTokenRequest,
    ChangePasswordRequest
)
from app.schemas.user import UserResponse, UserCreate

# =============================================
# ROUTER AND DEPENDENCIES
# =============================================
router = APIRouter()
security = HTTPBearer()
settings = get_settings()

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
):
    """Get current authenticated user from JWT token"""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# =============================================
# AUTHENTICATION ROUTES
# =============================================

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User email
    - **password**: User password
    
    Returns:
    - **access_token**: JWT access token (expires in 30 minutes)
    - **refresh_token**: JWT refresh token (expires in 7 days)
    - **token_type**: Always "bearer"
    - **user**: User information
    """
    # Get user by email
    user = await user_service.get_user_by_email(login_data.email)
    if not user:
        raise InvalidCredentialsError()
    
    # Verify password
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(user_service.user_repo.db)
    db_user = await user_repo.get_by_email(login_data.email)
    
    if not db_user or not verify_password(login_data.password, db_user.password):
        raise InvalidCredentialsError()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.user_email, "type": user.user_type},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_access_token(
        data={"sub": str(user.user_id), "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register new user and return JWT tokens
    
    - **user_name**: Full name
    - **user_email**: Email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **user_type**: User type (candidate, recruiter, company_owner, admin)
    - **is_work**: Whether this is a work account
    - **birth_day**: Date of birth (optional)
    """
    # Create user
    user = await user_service.create_user(user_data)
    
    # Create tokens for new user
    access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.user_email, "type": user.user_type},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_access_token(
        data={"sub": str(user.user_id), "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Refresh JWT access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token with same expiration time.
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.user_id), "email": user.user_email, "type": user.user_type},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header:
    Authorization: Bearer <token>
    """
    return current_user

@router.post("/logout")
async def logout():
    """
    Logout user
    
    Note: Since JWT tokens are stateless, logout is handled client-side
    by removing the token from storage. This endpoint is here for consistency.
    """
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change user password
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    
    Requires authentication.
    """
    # Get user with password from database
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(user_service.user_repo.db)
    db_user = await user_repo.get_by_id(current_user.user_id)
    
    if not db_user:
        raise UserNotFoundError()
    
    # Verify current password
    if not verify_password(password_data.current_password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    from app.schemas.user import UserUpdate
    from app.core.security import get_password_hash
    
    user_update = UserUpdate()
    # Need to hash the password
    user_repo_update = await user_repo.update_password(
        current_user.user_id, 
        get_password_hash(password_data.new_password)
    )
    
    return {"message": "Password changed successfully"}

# =============================================
# AUTHORIZATION HELPERS
# =============================================

def require_user_type(allowed_types: list[str]):
    """Decorator to require specific user types"""
    def decorator(current_user: UserResponse = Depends(get_current_user)):
        if current_user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required user types: {allowed_types}"
            )
        return current_user
    return decorator

# Common authorization dependencies
def require_admin(current_user: UserResponse = Depends(get_current_user)):
    """Require admin user type"""
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_recruiter_or_admin(current_user: UserResponse = Depends(get_current_user)):
    """Require recruiter or admin user type"""
    if current_user.user_type not in ["recruiter", "admin", "company_owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter or admin access required"
        )
    return current_user

def require_candidate(current_user: UserResponse = Depends(get_current_user)):
    """Require candidate user type"""
    if current_user.user_type != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required"
        )
    return current_user