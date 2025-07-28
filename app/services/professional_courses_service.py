# =============================================
# app/services/professional_courses_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.professional_courses_repository import ProfessionalCoursesRepository
from app.repositories.user_repository import UserRepository
from app.schemas.professional_courses import (
    ProfessionalCoursesCreate,
    ProfessionalCoursesUpdate,
    ProfessionalCoursesResponse,
    ProfessionalCoursesDetail,
    ProfessionalCoursesSummary,
    ProfessionalCoursesSearchFilters,
    ProfessionalCoursesStatistics,
    BulkCoursesCreate,
    BulkCoursesResponse,
    CertificateInfo
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class ProfessionalCoursesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.courses_repo = ProfessionalCoursesRepository(db)
        self.user_repo = UserRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_course(self, course_data: ProfessionalCoursesCreate, create_user_id: Optional[UUID] = None) -> ProfessionalCoursesResponse:
        """Create a new professional course with business validations"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(course_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Create course
            course = await self.courses_repo.create(course_data, create_user_id)
            
            logger.info(f"Professional course created successfully: {course.course_name} (ID: {course.professional_courses_id})")
            return ProfessionalCoursesResponse.model_validate(course)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating professional course: {e}")
            raise AppException(f"Erro ao criar curso profissional: {str(e)}")
    
    async def get_course(self, course_id: UUID) -> ProfessionalCoursesDetail:
        """Get professional course by ID with detailed information"""
        try:
            course = await self.courses_repo.get_by_id(course_id)
            if not course:
                raise AppException("Curso profissional não encontrado")
            
            # Get user information
            user = await self.user_repo.get_by_id(course.user_id)
            
            # Convert to detail response with additional info
            course_detail = ProfessionalCoursesDetail.model_validate(course)
            
            # Add user information
            if user:
                course_detail.user_name = user.user_name
            
            # Add certificate information
            course_detail.has_pdf_certificate = course.certification_media_pdf is not None
            course_detail.has_image_certificate = course.certification_media_image is not None
            
            return course_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting professional course {course_id}: {e}")
            raise AppException(f"Erro ao buscar curso profissional: {str(e)}")
    
    async def get_courses(self, skip: int = 0, limit: int = 100) -> List[ProfessionalCoursesResponse]:
        """Get all professional courses with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            courses = await self.courses_repo.get_all(skip=skip, limit=limit)
            return [ProfessionalCoursesResponse.model_validate(course) for course in courses]
            
        except Exception as e:
            logger.error(f"Error getting professional courses: {e}")
            raise AppException(f"Erro ao listar cursos profissionais: {str(e)}")
    
    async def update_course(self, course_id: UUID, course_data: ProfessionalCoursesUpdate) -> ProfessionalCoursesDetail:
        """Update professional course with business validations"""
        try:
            # Check if course exists
            existing_course = await self.courses_repo.get_by_id(course_id)
            if not existing_course:
                raise AppException("Curso profissional não encontrado")
            
            # Update course
            updated_course = await self.courses_repo.update(course_id, course_data)
            if not updated_course:
                raise AppException("Erro ao atualizar curso profissional")
            
            logger.info(f"Professional course updated successfully: {course_id}")
            return await self.get_course(course_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating professional course {course_id}: {e}")
            raise AppException(f"Erro ao atualizar curso profissional: {str(e)}")
    
    async def delete_course(self, course_id: UUID) -> bool:
        """Delete professional course (soft delete)"""
        try:
            # Check if course exists
            course = await self.courses_repo.get_by_id(course_id)
            if not course:
                raise AppException("Curso profissional não encontrado")
            
            success = await self.courses_repo.soft_delete(course_id)
            if success:
                logger.info(f"Professional course deleted successfully: {course_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting professional course {course_id}: {e}")
            raise AppException(f"Erro ao deletar curso profissional: {str(e)}")
    
    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================
    
    async def get_user_courses(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalCoursesSummary]:
        """Get all professional courses for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            courses = await self.courses_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary
            course_summaries = []
            for course in courses:
                summary = ProfessionalCoursesSummary.model_validate(course)
                summary.has_certificate = (course.certification_media_pdf is not None or 
                                         course.certification_media_image is not None)
                course_summaries.append(summary)
            
            return course_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user courses {user_id}: {e}")
            raise AppException(f"Erro ao buscar cursos profissionais do usuário: {str(e)}")
    
    async def get_user_completed_courses(self, user_id: UUID) -> List[ProfessionalCoursesResponse]:
        """Get user's completed courses"""
        try:
            courses = await self.courses_repo.get_user_completed_courses(user_id)
            return [ProfessionalCoursesResponse.model_validate(course) for course in courses]
            
        except Exception as e:
            logger.error(f"Error getting completed courses for user {user_id}: {e}")
            raise AppException(f"Erro ao buscar cursos concluídos: {str(e)}")
    
    async def get_user_ongoing_courses(self, user_id: UUID) -> List[ProfessionalCoursesResponse]:
        """Get user's ongoing courses"""
        try:
            courses = await self.courses_repo.get_user_ongoing_courses(user_id)
            return [ProfessionalCoursesResponse.model_validate(course) for course in courses]
            
        except Exception as e:
            logger.error(f"Error getting ongoing courses for user {user_id}: {e}")
            raise AppException(f"Erro ao buscar cursos em andamento: {str(e)}")
    
    async def get_user_courses_with_certificates(self, user_id: UUID) -> List[ProfessionalCoursesResponse]:
        """Get user's courses that have certificates"""
        try:
            courses = await self.courses_repo.get_user_courses_with_certificates(user_id)
            return [ProfessionalCoursesResponse.model_validate(course) for course in courses]
            
        except Exception as e:
            logger.error(f"Error getting courses with certificates for user {user_id}: {e}")
            raise AppException(f"Erro ao buscar cursos com certificados: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_courses(self, filters: ProfessionalCoursesSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalCoursesSummary]:
        """Search professional courses with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            courses = await self.courses_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            course_summaries = []
            for course in courses:
                summary = ProfessionalCoursesSummary.model_validate(course)
                summary.has_certificate = (course.certification_media_pdf is not None or 
                                         course.certification_media_image is not None)
                course_summaries.append(summary)
            
            return course_summaries
            
        except Exception as e:
            logger.error(f"Error searching professional courses: {e}")
            raise AppException(f"Erro ao buscar cursos profissionais: {str(e)}")
    
    async def get_courses_count(self, filters: Optional[ProfessionalCoursesSearchFilters] = None) -> int:
        """Get total count of professional courses matching filters"""
        try:
            return await self.courses_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting courses count: {e}")
            raise AppException(f"Erro ao contar cursos profissionais: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_user_statistics(self, user_id: UUID) -> ProfessionalCoursesStatistics:
        """Get comprehensive statistics for user's professional courses"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Get statistics from repository
            stats = await self.courses_repo.get_user_statistics(user_id)
            
            # Get courses by year for trends
            courses_by_year = await self.courses_repo.get_courses_by_year(user_id)
            
            return ProfessionalCoursesStatistics(
                user_id=user_id,
                total_courses=stats["total_courses"],
                completed_courses=stats["completed_courses"],
                ongoing_courses=stats["ongoing_courses"],
                total_study_hours=stats["total_study_hours"],
                avg_course_duration_hours=stats["avg_course_duration_hours"],
                institutions_attended=stats["institutions_attended"],
                certificates_earned=stats["certificates_earned"],
                courses_by_year=courses_by_year
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user course statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas de cursos: {str(e)}")
    
    async def get_top_institutions(self, limit: int = 10) -> List[Dict]:
        """Get top institutions by number of courses"""
        try:
            return await self.courses_repo.get_top_institutions(limit)
        except Exception as e:
            logger.error(f"Error getting top institutions: {e}")
            raise AppException(f"Erro ao obter principais instituições: {str(e)}")
    
    # =============================================
    # BULK OPERATIONS
    # =============================================
    
    async def bulk_create_courses(self, bulk_data: BulkCoursesCreate, create_user_id: Optional[UUID] = None) -> BulkCoursesResponse:
        """Create multiple professional courses in batch"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(bulk_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Create courses
            courses_data = [course for course in bulk_data.courses]
            created_courses = await self.courses_repo.bulk_create(courses_data, create_user_id)
            
            # Convert to response
            created_responses = [ProfessionalCoursesResponse.model_validate(course) for course in created_courses]
            
            logger.info(f"Bulk created {len(created_courses)} professional courses for user {bulk_data.user_id}")
            
            return BulkCoursesResponse(
                created_courses=created_responses,
                failed_courses=[],
                total_created=len(created_courses),
                total_failed=0
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error bulk creating courses: {e}")
            raise AppException(f"Erro ao criar cursos em lote: {str(e)}")
    
    # =============================================
    # CERTIFICATE MANAGEMENT
    # =============================================
    
    async def get_certificate_info(self, course_id: UUID) -> CertificateInfo:
        """Get certificate information for a course"""
        try:
            course = await self.courses_repo.get_by_id(course_id)
            if not course:
                raise AppException("Curso profissional não encontrado")
            
            return CertificateInfo(
                professional_courses_id=course_id,
                has_pdf=course.certification_media_pdf is not None,
                has_image=course.certification_media_image is not None,
                upload_date=course.created_date,
                file_size_bytes=len(course.certification_media_pdf) if course.certification_media_pdf else 0,
                download_urls={}  # URLs would be generated based on file storage service
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting certificate info: {e}")
            raise AppException(f"Erro ao obter informações do certificado: {str(e)}")
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def course_exists(self, course_id: UUID) -> bool:
        """Check if professional course exists"""
        try:
            return await self.courses_repo.exists(course_id)
        except Exception as e:
            logger.error(f"Error checking if course exists: {e}")
            return False
    
    async def user_has_courses(self, user_id: UUID) -> bool:
        """Check if user has professional courses"""
        try:
            count = await self.courses_repo.get_user_courses_count(user_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if user has courses: {e}")
            return False
    
    async def validate_course_data(self, course_data: ProfessionalCoursesCreate) -> Dict[str, List[str]]:
        """Validate course data and return validation errors"""
        try:
            errors = {}
            
            # Validate user exists
            if not await self.user_repo.exists(course_data.user_id):
                errors.setdefault("user_id", []).append("Usuário não encontrado")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating course data: {e}")
            return {"general": ["Erro na validação dos dados"]}