# =============================================
# app/api/v1/router.py
# =============================================
from fastapi import APIRouter, Depends,HTTPException, status

from app.api.v1.endpoints import (
    users,
    companies,
    jobs,
    professional_profiles,
    professional_courses,
    professional_experience,
    academic_background,
    applications,
    analyses,
    curriculum,
    auth
)
from app.config.database import get_db

from app.config.settings import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
# Get settings
settings = get_settings()


# =============================================
# API V1 ROUTER
# =============================================
api_router = APIRouter()

# =============================================
# AUTHENTICATION ROUTES
# =============================================
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

# =============================================
# USER MANAGEMENT ROUTES
# =============================================
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    responses={
        404: {"description": "User not found"},
        409: {"description": "User already exists"}
    }
)

# =============================================
# COMPANY MANAGEMENT ROUTES
# =============================================
api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["Companies"],
    responses={
        404: {"description": "Company not found"},
        409: {"description": "Company already exists"}
    }
)

# =============================================
# JOB MANAGEMENT ROUTES
# =============================================
api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
    responses={
        404: {"description": "Job not found"},
        409: {"description": "Job code already exists"}
    }
)

# =============================================
# PROFESSIONAL PROFILE ROUTES
# =============================================
api_router.include_router(
    professional_profiles.router,
    prefix="/professional-profiles",
    tags=["Professional Profiles"],
    responses={
        404: {"description": "Profile not found"},
        400: {"description": "Invalid profile data"}
    }
)

# =============================================
# PROFESSIONAL COURSES ROUTES
# =============================================
api_router.include_router(
    professional_courses.router,
    prefix="/professional-courses",
    tags=["Professional Courses"],
    responses={
        404: {"description": "Course not found"},
        400: {"description": "Invalid course data"}
    }
)

# =============================================
# PROFESSIONAL EXPERIENCE ROUTES
# =============================================
api_router.include_router(
    professional_experience.router,
    prefix="/professional-experience",
    tags=["Professional Experience"],
    responses={
        404: {"description": "Experience not found"},
        400: {"description": "Invalid experience data"},
        409: {"description": "User already has current experience"}
    }
)

# =============================================
# ACADEMIC BACKGROUND ROUTES
# =============================================
api_router.include_router(
    academic_background.router,
    prefix="/academic-background",
    tags=["Academic Background"],
    responses={
        404: {"description": "Academic background not found"},
        400: {"description": "Invalid academic data"}
    }
)

# =============================================
# CURRICULUM MANAGEMENT ROUTES
# =============================================
api_router.include_router(
    curriculum.router,
    prefix="/curriculum",
    tags=["Curriculum"],
    responses={
        404: {"description": "Curriculum not found"},
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"}
    }
)

# =============================================
# APPLICATION ROUTES
# =============================================
api_router.include_router(
    applications.router,
    prefix="/applications",
    tags=["Job Applications"],
    responses={
        404: {"description": "Application not found"},
        409: {"description": "User already applied to this job"},
        400: {"description": "Invalid application data"}
    }
)

# =============================================
# ANALYSIS ROUTES
# =============================================
api_router.include_router(
    analyses.router,
    prefix="/analyses",
    tags=["Resume Analyses"],
    responses={
        404: {"description": "Analysis not found"},
        400: {"description": "Invalid analysis request"},
        503: {"description": "LLM service unavailable"}
    }
)

# =============================================
# USER MANAGEMENT ROUTES
# =============================================
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    responses={
        404: {"description": "User not found"},
        409: {"description": "User already exists"}
    }
)

# =============================================
# PROFESSIONAL COURSES ROUTES
# =============================================
api_router.include_router(
    professional_courses.router,
    prefix="/professional-courses",
    tags=["Professional Courses"],
    responses={
        404: {"description": "Course not found"},
        400: {"description": "Invalid course data"}
    }
)

# =============================================
# PROFESSIONAL EXPERIENCE ROUTES
# =============================================
api_router.include_router(
    professional_experience.router,
    prefix="/professional-experience",
    tags=["Professional Experience"],
    responses={
        404: {"description": "Experience not found"},
        400: {"description": "Invalid experience data"}
    }
)

# =============================================
# ACADEMIC BACKGROUND ROUTES
# =============================================
api_router.include_router(
    academic_background.router,
    prefix="/academic-background",
    tags=["Academic Background"],
    responses={
        404: {"description": "Academic background not found"},
        400: {"description": "Invalid academic data"}
    }
)

# =============================================
# AUTHENTICATION ROUTES
# =============================================
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


# =============================================
# HEALTH CHECK ROUTE
# =============================================
@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the current status of the API and its dependencies.
    """
    return {
        "status": "healthy",
        "message": "Resume Analyzer API is running",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "companies": "/api/v1/companies",
            "jobs": "/api/v1/jobs",
            "professional_profiles": "/api/v1/professional-profiles",
            "professional_courses": "/api/v1/professional-courses",
            "professional_experience": "/api/v1/professional-experience",
            "academic_background": "/api/v1/academic-background",
            "curriculum": "/api/v1/curriculum",
            "applications": "/api/v1/applications",
            "analysis": "/api/v1/analysis"
        }
    }

# =============================================
# API INFO ROUTE
# =============================================
@api_router.get("/info", tags=["Info"])
async def api_info():
    """
    API information endpoint
    
    Returns detailed information about the API capabilities and features.
    """
    return {
        "name": "Resume Analyzer API",
        "version": "1.0.0",
        "description": "Sistema inteligente para análise automatizada de currículos usando LLM",
        "features": [
            "Gestão de usuários e empresas",
            "Cadastro de vagas de emprego",
            "Perfis profissionais completos",
            "Upload e análise de currículos",
            "Análise de compatibilidade com IA",
            "Rankings e relatórios",
            "Estatísticas e analytics"
        ],
        "supported_formats": ["PDF", "DOC", "DOCX", "TXT"],
        "llm_providers": ["OpenAI", "Anthropic", "Groq", "Gemini"],
        "authentication": "JWT Bearer Token",
        "documentation": "/docs"
    }

# Health and info endpoints
@api_router.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint with database connectivity test
    """
    try:
        # Test database connection
        await db.execute("SELECT 1")
        database_status = "connected"
    except Exception:
        database_status = "disconnected"
    
    return {
        "status": "healthy" if database_status == "connected" else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": database_status,
        "llm_providers": settings.available_llm_providers,
        "timestamp": "2025-01-27T00:00:00Z"  # You might want to use datetime.now()
    }

@api_router.get("/info", tags=["Info"])
async def get_api_info():
    """
    Get API information and configuration
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "llm_config": {
            "default_provider": settings.DEFAULT_LLM_PROVIDER,
            "available_providers": settings.available_llm_providers,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": settings.LLM_TEMPERATURE
        },
        "analysis_weights": settings.get_score_weights(),
        "features": {
            "file_upload": True,
            "llm_analysis": settings.has_llm_provider,
            "real_time_analysis": True,
            "pdf_reports": True,
            "analytics": True
        }
    }
