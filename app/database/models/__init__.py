# =============================================
# app/database/models/__init__.py
# =============================================

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .company import Company
from .job import Job
from .professional_profile import ProfessionalProfile
from .professional_experience import ProfessionalExperience
from .academic_background import AcademicBackground
from .professional_courses import ProfessionalCourses
from .curriculum import Curriculum
from .application_job import ApplicationJob
from .analyze_application_job import AnalyzeApplicationJob
from .address import Address

# Make all models available for import
__all__ = [
    "User",
    "Company", 
    "Job",
    "ProfessionalProfile",
    "ProfessionalExperience", 
    "AcademicBackground",
    "ProfessionalCourses",
    "Curriculum",
    "ApplicationJob",
    "AnalyzeApplicationJob", 
    "Address"
]