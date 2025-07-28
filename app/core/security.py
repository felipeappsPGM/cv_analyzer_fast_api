# =============================================
# app/core/security.py
# =============================================
"""Security utilities for authentication and authorization"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import secrets
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config.settings import get_settings

# Get settings
settings = get_settings()

# =============================================
# PASSWORD HASHING
# =============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def generate_password(length: int = 12) -> str:
    """Generate a secure random password"""
    import string
    
    # Character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill the rest with random characters
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

# =============================================
# JWT TOKEN MANAGEMENT
# =============================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Check if token has expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for debugging)"""
    try:
        return jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
    except JWTError:
        return None

# =============================================
# API KEY MANAGEMENT
# =============================================

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key

# =============================================
# SESSION MANAGEMENT
# =============================================

def generate_session_id() -> str:
    """Generate a secure session ID"""
    return secrets.token_urlsafe(32)

def create_session_token(user_id: str, session_id: str) -> str:
    """Create a session token"""
    data = {
        "sub": user_id,
        "session_id": session_id,
        "type": "session"
    }
    
    return create_access_token(
        data, 
        expires_delta=timedelta(hours=24)
    )

# =============================================
# PASSWORD RESET TOKENS
# =============================================

def create_password_reset_token(email: str) -> str:
    """Create a password reset token"""
    data = {
        "email": email,
        "type": "password_reset"
    }
    
    return create_access_token(
        data,
        expires_delta=timedelta(hours=1)  # Reset tokens expire in 1 hour
    )

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email"""
    try:
        payload = verify_token(token)
        
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("email")
        
    except HTTPException:
        return None

# =============================================
# EMAIL VERIFICATION TOKENS
# =============================================

def create_email_verification_token(email: str) -> str:
    """Create an email verification token"""
    data = {
        "email": email,
        "type": "email_verification"
    }
    
    return create_access_token(
        data,
        expires_delta=timedelta(days=7)  # Verification tokens expire in 7 days
    )

def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify email verification token and return email"""
    try:
        payload = verify_token(token)
        
        if payload.get("type") != "email_verification":
            return None
        
        return payload.get("email")
        
    except HTTPException:
        return None

# =============================================
# SECURITY UTILITIES
# =============================================

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def generate_numeric_code(length: int = 6) -> str:
    """Generate a numeric code (for OTP, etc.)"""
    return ''.join(secrets.choice('0123456789') for _ in range(length))

def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks"""
    return secrets.compare_digest(a.encode(), b.encode())

def is_safe_url(url: str, allowed_hosts: list[str]) -> bool:
    """Check if a URL is safe for redirection"""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        # Only allow http/https
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check if host is in allowed list
        if parsed.netloc and parsed.netloc not in allowed_hosts:
            return False
        
        return True
        
    except Exception:
        return False

# =============================================
# RATE LIMITING UTILITIES
# =============================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._attempts = {}
    
    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Check if an action is allowed for a given key"""
        now = datetime.utcnow()
        
        if key not in self._attempts:
            self._attempts[key] = []
        
        # Remove old attempts outside the window
        cutoff = now - timedelta(seconds=window_seconds)
        self._attempts[key] = [
            attempt for attempt in self._attempts[key] 
            if attempt > cutoff
        ]
        
        # Check if under limit
        if len(self._attempts[key]) >= max_attempts:
            return False
        
        # Record this attempt
        self._attempts[key].append(now)
        return True
    
    def reset(self, key: str):
        """Reset attempts for a key"""
        if key in self._attempts:
            del self._attempts[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

# =============================================
# SECURITY HEADERS
# =============================================

def get_security_headers() -> Dict[str, str]:
    """Get recommended security headers"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self';"
    }

# =============================================
# INPUT SANITIZATION
# =============================================

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Basic input sanitization"""
    if not input_string:
        return ""
    
    # Limit length
    sanitized = input_string[:max_length]
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized

def is_valid_email_format(email: str) -> bool:
    """Validate email format"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None