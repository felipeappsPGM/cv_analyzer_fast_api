# =============================================
# app/main.py (Atualizado com Exception Handlers)
# =============================================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

from app.api.v1.router import api_router
from app.config.settings import settings
from app.core.exceptions import AppException, UserNotFoundError, UserAlreadyExistsError
from app.core.exception_handlers import (
    app_exception_handler,
    user_not_found_handler,
    user_already_exists_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    global_exception_handler,
    http_exception_handler
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Criar instância da aplicação
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="API para gerenciamento de usuários com autenticação JWT",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "users",
            "description": "Operações relacionadas a usuários",
        },
        {
            "name": "health",
            "description": "Health checks da aplicação",
        }
    ]
)

# ==========================================
# MIDDLEWARE
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# EXCEPTION HANDLERS (usando @app)
# ==========================================

# Exceções customizadas específicas
@app.exception_handler(UserNotFoundError)
async def handle_user_not_found(request, exc):
    return await user_not_found_handler(request, exc)

@app.exception_handler(UserAlreadyExistsError)
async def handle_user_already_exists(request, exc):
    return await user_already_exists_handler(request, exc)

# Exceções customizadas gerais
@app.exception_handler(AppException)
async def handle_app_exception(request, exc):
    return await app_exception_handler(request, exc)

# Exceções do banco de dados
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request, exc):
    return await integrity_error_handler(request, exc)

@app.exception_handler(SQLAlchemyError)
async def handle_sqlalchemy_error(request, exc):
    return await sqlalchemy_error_handler(request, exc)

# HTTP Exceptions do FastAPI
@app.exception_handler(HTTPException)
async def handle_http_exception(request, exc):
    return await http_exception_handler(request, exc)

# Handler global (deve ser o último)
@app.exception_handler(Exception)
async def handle_global_exception(request, exc):
    return await global_exception_handler(request, exc)

# ==========================================
# ROUTERS
# ==========================================
app.include_router(api_router, prefix="/api/v1")

# ==========================================
# ROUTES BÁSICAS
# ==========================================
@app.get("/")
async def root():
    return {
        "message": "FastAPI Users API", 
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.version}

# ==========================================
# STARTUP/SHUTDOWN EVENTS
# ==========================================
@app.on_event("startup")
async def startup_event():
    logging.info(f"🚀 {settings.app_name} v{settings.version} iniciada")
    logging.info(f"🔧 Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info(f"🛑 {settings.app_name} encerrada")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )