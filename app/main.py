# =============================================
# app/main.py (Atualizado com Exception Handlers)
# =============================================
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time
import uvicorn
from app.config.settings import get_settings
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
from app.config.database import create_tables
from contextlib import asynccontextmanager
# =============================================
# LOGGING CONFIGURATION
# =============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================
# SETTINGS
# =============================================
settings = get_settings()

# =============================================
# LIFESPAN CONTEXT MANAGER
# =============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting Resume Analyzer API...")
    
    # Create database tables
    logger.info("Creating database tables...")
    await create_tables()
    logger.info("Database tables created successfully")
    
    # Initialize other services here if needed
    # await initialize_llm_services()
    # await initialize_cache()
    
    logger.info("Resume Analyzer API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Analyzer API...")
    # Cleanup tasks here if needed
    logger.info("Resume Analyzer API shut down successfully")

# =============================================
# FASTAPI APPLICATION
# =============================================
app = FastAPI(
    title="Resume Analyzer API",
    description="""
    Sistema inteligente para análise automatizada de currículos usando Large Language Models (LLM).
    
    ## Principais Funcionalidades
    
    * **Gestão de Usuários**: Registro e autenticação de candidatos, recrutadores e empresas
    * **Gestão de Vagas**: Cadastro e gerenciamento de vagas de emprego
    * **Perfis Profissionais**: Criação de perfis completos com experiência, formação e cursos
    * **Upload de Currículos**: Suporte para PDF, DOC, DOCX e TXT
    * **Análise Inteligente**: Análise automática de compatibilidade usando IA
    * **Rankings e Relatórios**: Classificação de candidatos e geração de relatórios
    * **Analytics**: Estatísticas e métricas detalhadas
    
    ## Tecnologias
    
    * **LLM Providers**: OpenAI, Anthropic, Groq, Gemini
    * **Workflow Engine**: LangGraph
    * **Database**: PostgreSQL
    * **Authentication**: JWT Bearer Tokens
    
    ## Pontuação de Análise
    
    O sistema utiliza um algoritmo de pontuação ponderada:
    
    * **Experiência Profissional**: 35%
    * **Formação Acadêmica**: 30% 
    * **Cursos Profissionalizantes**: 20%
    * **Pontos Fortes**: +15%
    * **Pontos Fracos**: -10%
    
    Score Final = (Experiência × 0.35) + (Formação × 0.30) + (Cursos × 0.20) + (Pontos Fortes × 0.15) - (Pontos Fracos × 0.10)
    """,
    version="1.0.0",
    contact={
        "name": "Resume Analyzer Team",
        "email": "support@resume-analyzer.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operações de autenticação e autorização",
        },
        {
            "name": "Users",
            "description": "Gestão de usuários do sistema",
        },
        {
            "name": "Companies", 
            "description": "Gestão de empresas",
        },
        {
            "name": "Jobs",
            "description": "Gestão de vagas de emprego",
        },
        {
            "name": "Professional Profiles",
            "description": "Gestão de perfis profissionais",
        },
        {
            "name": "Professional Courses",
            "description": "Gestão de cursos profissionalizantes",
        },
        {
            "name": "Professional Experience",
            "description": "Gestão de experiências profissionais",
        },
        {
            "name": "Academic Background",
            "description": "Gestão de formação acadêmica",
        },
        {
            "name": "Curriculum",
            "description": "Upload e gestão de currículos",
        },
        {
            "name": "Job Applications",
            "description": "Gestão de candidaturas a vagas",
        },
        {
            "name": "Resume Analysis",
            "description": "Análise automática de currículos com IA",
        },
        {
            "name": "Health",
            "description": "Health checks e status da API",
        },
        {
            "name": "Info",
            "description": "Informações sobre a API",
        },
    ],
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# =============================================
# MIDDLEWARE CONFIGURATION
# =============================================

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.4f}s"
    )
    
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)

# Trusted Host Middleware (for production)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
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
        "version": settings.VERSION,  # era settings.version
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.VERSION} 

# ==========================================
# STARTUP/SHUTDOWN EVENTS
# ==========================================
@app.on_event("startup")
async def startup_event():
    logging.info(f"🚀 {settings.app_name} v{settings.VERSION} iniciada")
    logging.info(f"🔧 Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info(f"🛑 {settings.app_name} encerrada")

# =============================================
# DEVELOPMENT SERVER
# =============================================
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG
    )