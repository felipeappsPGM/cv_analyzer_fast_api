# =============================================
# app/schemas/auth.py
# =============================================
from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.user import UserResponse

# =============================================
# LOGIN SCHEMAS
# =============================================
class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Valid refresh token")

# =============================================
# PASSWORD MANAGEMENT SCHEMAS
# =============================================
class ChangePasswordRequest(BaseModel):
    """Schema for change password request"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., description="User email address")

class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

# =============================================
# USER CLAIMS AND PERMISSIONS
# =============================================
class UserClaims(BaseModel):
    """Schema for JWT user claims"""
    user_id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    user_type: str = Field(..., description="User type")
    company_id: Optional[UUID] = Field(None, description="Company ID if user belongs to company")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    issued_at: datetime = Field(..., description="Token issued at")
    expires_at: datetime = Field(..., description="Token expires at")

class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    user_type: Optional[str] = None
    company_id: Optional[UUID] = None

# =============================================
# PERMISSION SCHEMAS
# =============================================
class Permission(BaseModel):
    """Schema for user permission"""
    model_config = ConfigDict(from_attributes=True)
    
    permission_id: UUID
    name: str = Field(..., description="Permission name")
    description: str = Field(..., description="Permission description")
    resource: str = Field(..., description="Resource this permission applies to")
    action: str = Field(..., description="Action this permission allows")

class Role(BaseModel):
    """Schema for user role"""
    model_config = ConfigDict(from_attributes=True)
    
    role_id: UUID
    name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")
    permissions: List[Permission] = Field(default_factory=list, description="Role permissions")

# =============================================
# API KEY SCHEMAS (for future use)
# =============================================
class ApiKeyCreate(BaseModel):
    """Schema for creating API key"""
    name: str = Field(..., max_length=255, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_at: Optional[datetime] = Field(None, description="API key expiration")
    permissions: List[str] = Field(default_factory=list, description="API key permissions")

class ApiKeyResponse(BaseModel):
    """Schema for API key response"""
    model_config = ConfigDict(from_attributes=True)
    
    api_key_id: UUID
    name: str
    description: Optional[str] = None
    key_preview: str = Field(..., description="First 8 characters of API key")
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    permissions: List[str] = Field(default_factory=list)

# =============================================
# SESSION SCHEMAS
# =============================================
class SessionInfo(BaseModel):
    """Schema for user session information"""
    session_id: str = Field(..., description="Session identifier")
    user_id: UUID = Field(..., description="User ID")
    ip_address: str = Field(..., description="Client IP address")
    user_agent: str = Field(..., description="Client user agent")
    created_at: datetime = Field(..., description="Session created at")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expires at")
    is_active: bool = Field(True, description="Whether session is active")

# =============================================
# AUDIT SCHEMAS
# =============================================
class LoginAttempt(BaseModel):
    """Schema for login attempt logging"""
    email: str = Field(..., description="Email used in login attempt")
    success: bool = Field(..., description="Whether login was successful")
    ip_address: str = Field(..., description="Client IP address")
    user_agent: str = Field(..., description="Client user agent")
    attempted_at: datetime = Field(..., description="When login was attempted")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if unsuccessful")

class SecurityEvent(BaseModel):
    """Schema for security event logging"""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[UUID] = Field(None, description="User ID if applicable")
    ip_address: str = Field(..., description="Client IP address")
    description: str = Field(..., description="Event description")
    metadata: dict = Field(default_factory=dict, description="Additional event metadata")
    occurred_at: datetime = Field(..., description="When event occurred")
    severity: str = Field(..., description="Event severity level")

# =============================================
# VALIDATION HELPERS
# =============================================
class PasswordStrengthCheck(BaseModel):
    """Schema for password strength validation"""
    password: str = Field(..., description="Password to check")
    
    @validator('password')
    def check_password_strength(cls, v):
        """Comprehensive password strength validation"""
        errors = []
        
        if len(v) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(v) > 128:
            errors.append("Password must be less than 128 characters long")
        
        if not any(c.isupper() for c in v):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            errors.append("Password must contain at least one number")
        
        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            "password", "123456", "qwerty", "abc123", "password123",
            "admin", "letmein", "welcome", "monkey", "dragon"
        ]
        if v.lower() in weak_passwords:
            errors.append("Password is too common and weak")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return v

# =============================================
# RESPONSE MESSAGES
# =============================================
class AuthMessage(BaseModel):
    """Schema for authentication messages"""
    message: str = Field(..., description="Message text")
    success: bool = Field(..., description="Whether operation was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")