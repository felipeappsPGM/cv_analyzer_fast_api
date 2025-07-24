# =============================================
# app/core/exception_handlers.py
# =============================================
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

from app.core.exceptions import AppException, UserNotFoundError, UserAlreadyExistsError

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