# =============================================
# app/database/models/__init__.py
# =============================================
"""
Database Models Package

Importa todos os modelos para garantir que sejam registrados no SQLAlchemy.
Este arquivo garante que o Alembic detecte todas as tabelas para migrações.
"""

# Importar todos os modelos para registro no Base.metadata
from .user import User
from .company import Company
from .job import Job
from .curriculum import Curriculum
from .professional_profile import ProfessionalProfile
from .professional_experience import ProfessionalExperience
from .academic_background import AcademicBackground
from .professional_courses import ProfessionalCourses
from .application_job import ApplicationJob
from .analyze_application_job import AnalyzeApplicationJob
from .address import Address

# Lista de todos os modelos para fácil acesso
__all__ = [
    "User",
    "Company", 
    "Job",
    "Curriculum",
    "ProfessionalProfile",
    "ProfessionalExperience",
    "AcademicBackground",
    "ProfessionalCourses",
    "ApplicationJob",
    "AnalyzeApplicationJob",
    "Address"
]

# Informação sobre os modelos
MODELS_INFO = {
    "total_models": len(__all__),
    "models": __all__,
    "description": "Sistema de Análise de Currículos com LLM"
}