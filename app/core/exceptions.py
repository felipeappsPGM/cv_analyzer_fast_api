# =============================================
# app/core/exceptions.py (VERSÃO EXPANDIDA)
# =============================================
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
from typing import Any, Dict, Optional
import traceback

logger = logging.getLogger(__name__)

# =============================================
# CUSTOM EXCEPTIONS
# =============================================

class AppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class UserNotFoundError(AppException):
    """Raised when user is not found"""
    pass

class UserAlreadyExistsError(AppException):
    """Raised when trying to create a user that already exists"""
    pass

class CompanyNotFoundError(AppException):
    """Raised when company is not found"""
    pass

class JobNotFoundError(AppException):
    """Raised when job is not found"""
    pass

class ProfileNotFoundError(AppException):
    """Raised when professional profile is not found"""
    pass

class ExperienceNotFoundError(AppException):
    """Raised when professional experience is not found"""
    pass

class CourseNotFoundError(AppException):
    """Raised when professional course is not found"""
    pass

class AcademicBackgroundNotFoundError(AppException):
    """Raised when academic background is not found"""
    pass

class ApplicationNotFoundError(AppException):
    """Raised when application is not found"""
    pass

class AnalysisNotFoundError(AppException):
    """Raised when analysis is not found"""
    pass

class CurriculumNotFoundError(AppException):
    """Raised when curriculum is not found"""
    pass

class ValidationError(AppException):
    """Raised when validation fails"""
    pass

class AuthenticationError(AppException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(AppException):
    """Raised when user lacks permissions"""
    pass

class LLMServiceError(AppException):
    """Raised when LLM service fails"""
    pass

class FileProcessingError(AppException):
    """Raised when file processing fails"""
    pass

class DatabaseError(AppException):
    """Raised when database operation fails"""
    pass

# =============================================
# EXCEPTION HANDLERS
# =============================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path)
            }
        }
    )

async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Handle user not found exceptions"""
    logger.warning(f"User not found: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "type": "UserNotFound",
                "message": exc.message,
                "path": str(request.url.path)
            }
        }
    )

async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    """Handle user already exists exceptions"""
    logger.warning(f"User already exists: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "type": "UserAlreadyExists",
                "message": exc.message,
                "path": str(request.url.path)
            }
        }
    )

async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path)
            }
        }
    )

async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle authentication errors"""
    logger.warning(f"Authentication error: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "type": "AuthenticationError",
                "message": exc.message,
                "path": str(request.url.path)
            }
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle authorization errors"""
    logger.warning(f"Authorization error: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "type": "AuthorizationError",
                "message": exc.message,
                "path": str(request.url.path)
            }
        }
    )

async def llm_service_error_handler(request: Request, exc: LLMServiceError) -> JSONResponse:
    """Handle LLM service errors"""
    logger.error(f"LLM service error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "type": "LLMServiceError",
                "message": "Serviço de análise temporariamente indisponível",
                "details": {"original_error": exc.message},
                "path": str(request.url.path)
            }
        }
    )

async def file_processing_error_handler(request: Request, exc: FileProcessingError) -> JSONResponse:
    """Handle file processing errors"""
    logger.error(f"File processing error: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "type": "FileProcessingError",
                "message": exc.message,
                "path": str(request.url.path)
            }
        }
    )

async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors"""
    logger.error(f"Database error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "DatabaseError",
                "message": "Erro interno do banco de dados",
                "path": str(request.url.path)
            }
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Log full traceback for debugging
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "Erro interno do servidor",
                "path": str(request.url.path)
            }
        }
    )


class AppException(Exception):
    """Base exception class for application-specific errors"""
    
    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundError(AppException):
    """Exception raised when a user is not found"""
    
    def __init__(self, user_id: Optional[str] = None, email: Optional[str] = None):
        if user_id:
            message = f"User with ID '{user_id}' not found"
        elif email:
            message = f"User with email '{email}' not found"
        else:
            message = "User not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "user_id": user_id,
                "email": email,
                "error_type": "USER_NOT_FOUND"
            }
        )


class UserAlreadyExistsError(AppException):
    """Exception raised when trying to create a user that already exists"""
    
    def __init__(self, email: str):
        message = f"User with email '{email}' already exists"
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={
                "email": email,
                "error_type": "USER_ALREADY_EXISTS"
            }
        )


class CompanyNotFoundError(AppException):
    """Exception raised when a company is not found"""
    
    def __init__(self, company_id: Optional[str] = None, cnpj: Optional[str] = None):
        if company_id:
            message = f"Company with ID '{company_id}' not found"
        elif cnpj:
            message = f"Company with CNPJ '{cnpj}' not found"
        else:
            message = "Company not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "company_id": company_id,
                "cnpj": cnpj,
                "error_type": "COMPANY_NOT_FOUND"
            }
        )


class JobNotFoundError(AppException):
    """Exception raised when a job is not found"""
    
    def __init__(self, job_id: str):
        message = f"Job with ID '{job_id}' not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "job_id": job_id,
                "error_type": "JOB_NOT_FOUND"
            }
        )


class ApplicationAlreadyExistsError(AppException):
    """Exception raised when user tries to apply to the same job twice"""
    
    def __init__(self, user_id: str, job_id: str):
        message = f"User '{user_id}' has already applied to job '{job_id}'"
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={
                "user_id": user_id,
                "job_id": job_id,
                "error_type": "APPLICATION_ALREADY_EXISTS"
            }
        )


class InvalidCredentialsError(AppException):
    """Exception raised when authentication credentials are invalid"""
    
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"error_type": "INVALID_CREDENTIALS"}
        )


class TokenExpiredError(AppException):
    """Exception raised when a token has expired"""
    
    def __init__(self):
        super().__init__(
            message="Token has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"error_type": "TOKEN_EXPIRED"}
        )


class InvalidTokenError(AppException):
    """Exception raised when a token is invalid"""
    
    def __init__(self):
        super().__init__(
            message="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"error_type": "INVALID_TOKEN"}
        )


class InsufficientPermissionsError(AppException):
    """Exception raised when user lacks required permissions"""
    
    def __init__(self, required_permission: str):
        message = f"Insufficient permissions. Required: {required_permission}"
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details={
                "required_permission": required_permission,
                "error_type": "INSUFFICIENT_PERMISSIONS"
            }
        )


class FileUploadError(AppException):
    """Exception raised when file upload fails"""
    
    def __init__(self, reason: str):
        message = f"File upload failed: {reason}"
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "reason": reason,
                "error_type": "FILE_UPLOAD_ERROR"
            }
        )


class LLMAnalysisError(AppException):
    """Exception raised when LLM analysis fails"""
    
    def __init__(self, provider: str, reason: str):
        message = f"LLM analysis failed with {provider}: {reason}"
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "provider": provider,
                "reason": reason,
                "error_type": "LLM_ANALYSIS_ERROR"
            }
        )


class ValidationError(AppException):
    """Exception raised when data validation fails"""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error in field '{field}': {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={
                "field": field,
                "validation_message": message,
                "error_type": "VALIDATION_ERROR"
            }
        )


class DatabaseError(AppException):
    """Exception raised when database operations fail"""
    
    def __init__(self, operation: str, reason: str):
        message = f"Database {operation} failed: {reason}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "operation": operation,
                "reason": reason,
                "error_type": "DATABASE_ERROR"
            }
        )


class ConfigurationError(AppException):
    """Exception raised when configuration is invalid"""
    
    def __init__(self, setting: str, reason: str):
        message = f"Configuration error in '{setting}': {reason}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "setting": setting,
                "reason": reason,
                "error_type": "CONFIGURATION_ERROR"
            }
        )

# =============================================
# EXCEPTION MAPPING
# =============================================

EXCEPTION_HANDLERS = {
    AppException: app_exception_handler,
    UserNotFoundError: user_not_found_handler,
    UserAlreadyExistsError: user_already_exists_handler,
    ValidationError: validation_error_handler,
    AuthenticationError: authentication_error_handler,
    AuthorizationError: authorization_error_handler,
    LLMServiceError: llm_service_error_handler,
    FileProcessingError: file_processing_error_handler,
    DatabaseError: database_error_handler,
    HTTPException: http_exception_handler,
    Exception: general_exception_handler
}