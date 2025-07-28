# =============================================
# app/core/exception_handlers.py
# =============================================
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AppException, UserNotFoundError, UserAlreadyExistsError

from app.core.exceptions import (
    AppException,
    UserNotFoundError,
    UserAlreadyExistsError,
    CompanyNotFoundError,
    JobNotFoundError,
    ApplicationAlreadyExistsError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientPermissionsError,
    FileUploadError,
    LLMAnalysisError,
    ValidationError,
    DatabaseError,
    ConfigurationError
)

logger = logging.getLogger(__name__)

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handler para exceções customizadas da aplicação"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Application Error",
            "message": exc.message,
            "type": exc.__class__.__name__
        }
    )

async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Handler específico para usuário não encontrado"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "User Not Found",
            "message": exc.message
        }
    )

async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    """Handler específico para usuário já existente"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "User Already Exists",
            "message": exc.message
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handler para erros de integridade do banco"""
    logger.error(f"Integrity error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Data Integrity Error",
            "message": "Violação de integridade dos dados"
        }
    )

async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handler para erros gerais do SQLAlchemy"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "Erro interno do banco de dados"
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler global para exceções não tratadas"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Erro interno do servidor"
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler para HTTPException do FastAPI"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    logger.error(f"Application exception: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "details": exc.details
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )


async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Handle user not found exceptions"""
    logger.warning(f"User not found: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "user_id": exc.details.get("user_id"),
        "email": exc.details.get("email")
    })
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "USER_NOT_FOUND",
            "details": exc.details
        }
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    """Handle user already exists exceptions"""
    logger.warning(f"User already exists: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "email": exc.details.get("email")
    })
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "USER_ALREADY_EXISTS",
            "details": exc.details
        }
    )


async def company_not_found_handler(request: Request, exc: CompanyNotFoundError) -> JSONResponse:
    """Handle company not found exceptions"""
    logger.warning(f"Company not found: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "company_id": exc.details.get("company_id"),
        "cnpj": exc.details.get("cnpj")
    })
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "COMPANY_NOT_FOUND",
            "details": exc.details
        }
    )


async def job_not_found_handler(request: Request, exc: JobNotFoundError) -> JSONResponse:
    """Handle job not found exceptions"""
    logger.warning(f"Job not found: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "job_id": exc.details.get("job_id")
    })
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "JOB_NOT_FOUND",
            "details": exc.details
        }
    )


async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
    """Handle invalid credentials exceptions"""
    logger.warning(f"Invalid credentials attempt", extra={
        "path": request.url.path,
        "method": request.method,
        "ip": request.client.host if request.client else "unknown"
    })
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "INVALID_CREDENTIALS"
        }
    )


async def token_expired_handler(request: Request, exc: TokenExpiredError) -> JSONResponse:
    """Handle token expired exceptions"""
    logger.info(f"Token expired", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "TOKEN_EXPIRED"
        }
    )


async def insufficient_permissions_handler(request: Request, exc: InsufficientPermissionsError) -> JSONResponse:
    """Handle insufficient permissions exceptions"""
    logger.warning(f"Insufficient permissions: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "required_permission": exc.details.get("required_permission")
    })
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "INSUFFICIENT_PERMISSIONS",
            "details": exc.details
        }
    )


async def file_upload_error_handler(request: Request, exc: FileUploadError) -> JSONResponse:
    """Handle file upload exceptions"""
    logger.error(f"File upload error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "reason": exc.details.get("reason")
    })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "FILE_UPLOAD_ERROR",
            "details": exc.details
        }
    )


async def llm_analysis_error_handler(request: Request, exc: LLMAnalysisError) -> JSONResponse:
    """Handle LLM analysis exceptions"""
    logger.error(f"LLM analysis error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "provider": exc.details.get("provider"),
        "reason": exc.details.get("reason")
    })
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": True,
            "message": exc.message,
            "error_type": "LLM_ANALYSIS_ERROR",
            "details": exc.details
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle SQLAlchemy integrity constraint violations"""
    logger.error(f"Database integrity error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    # Extract meaningful error message
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    # Common integrity errors
    if "unique constraint" in error_msg.lower():
        message = "A record with this information already exists"
        error_type = "DUPLICATE_RECORD"
    elif "foreign key constraint" in error_msg.lower():
        message = "Referenced record does not exist"
        error_type = "INVALID_REFERENCE"
    elif "not null constraint" in error_msg.lower():
        message = "Required field cannot be empty"
        error_type = "MISSING_REQUIRED_FIELD"
    else:
        message = "Database constraint violation"
        error_type = "CONSTRAINT_VIOLATION"
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": True,
            "message": message,
            "error_type": error_type,
            "details": {
                "database_error": error_msg
            }
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle general SQLAlchemy database errors"""
    logger.error(f"Database error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Database operation failed",
            "error_type": "DATABASE_ERROR",
            "details": {
                "database_error": str(exc)
            }
        }
    )


async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "error_type": "VALIDATION_ERROR",
            "details": {
                "validation_errors": errors
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "error_type": "HTTP_ERROR",
            "details": {
                "status_code": exc.status_code
            }
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__
    }, exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "error_type": "INTERNAL_ERROR",
            "details": {
                "exception_type": type(exc).__name__
            }
        }
    )