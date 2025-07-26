# =============================================
# app/services/application_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from app.repositories.application_job_repository import ApplicationJobRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.professional_profile_repository import ProfessionalProfileRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.application_job import (
    ApplicationJobCreate, 
    ApplicationJobUpdate, 
    ApplicationJobResponse, 
    ApplicationJobDetail, 
    ApplicationJobSummary,
    ApplicationJobSearchFilters,
    ApplicationJobStatistics,
    ApplicationJobBulkCreate,
    ApplicationJobBulkResponse
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.application_repo = ApplicationJobRepository(db)
        self.job_repo = JobRepository(db)
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfessionalProfileRepository(db)
        self.curriculum_repo = CurriculumRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def apply_to_job(self, user_id: UUID, job_id: UUID, professional_profile_id: Optional[UUID] = None) -> ApplicationJobResponse:
        """Apply to a job with business rule validations (BR08: One application per user per job)"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Validate job exists and is active
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            if job.deleted_date:
                raise AppException("Vaga não está mais ativa")
            
            # BR08: Check if user has already applied to this job
            already_applied = await self.application_repo.check_user_applied(user_id, job_id)
            if already_applied:
                raise AppException("Usuário já se candidatou para esta vaga")
            
            # Get or validate professional profile
            if not professional_profile_id:
                # Get user's primary profile
                profile = await self.profile_repo.get_user_primary_profile(user_id)
                if not profile:
                    raise AppException("Usuário deve ter um perfil profissional para se candidatar")
                professional_profile_id = profile.professional_profile_id
            else:
                # Validate provided profile belongs to user
                profile = await self.profile_repo.get_by_id(professional_profile_id)
                if not profile or profile.user_id != user_id:
                    raise AppException("Perfil profissional não encontrado ou não pertence ao usuário")
            
            # Check if user has a curriculum (recommended but not mandatory per BR07)
            user_curriculum = await self.curriculum_repo.get_user_active_curriculum(user_id)
            if not user_curriculum:
                logger.warning(f"User {user_id} applying without curriculum")
            
            # Create application
            application_data = ApplicationJobCreate(
                professional_profile_id=professional_profile_id,
                job_id=job_id,
                user_id=user_id
            )
            
            application = await self.application_repo.create(application_data, create_user_id=user_id)
            
            logger.info(f"Application created successfully: User {user_id} applied to job {job_id}")
            return ApplicationJobResponse.model_validate(application)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            raise AppException(f"Erro ao se candidatar: {str(e)}")
    
    async def get_application(self, application_id: UUID) -> ApplicationJobDetail:
        """Get application by ID with detailed information"""
        try:
            application = await self.application_repo.get_with_details(application_id)
            if not application:
                raise AppException("Candidatura não encontrada")
            
            # Convert to detail response with additional info
            app_detail = ApplicationJobDetail.model_validate(application)
            
            # Add user information
            if hasattr(application, 'user') and application.user:
                app_detail.user_name = application.user.user_name
                app_detail.user_email = application.user.user_email
            
            # Add job information
            if hasattr(application, 'job') and application.job:
                app_detail.job_name = application.job.job_name
                app_detail.job_code = application.job.code_vacancy_job
                
                # Add company information
                if hasattr(application.job, 'company') and application.job.company:
                    app_detail.company_name = application.job.company.company_name
            
            # Add profile information
            if hasattr(application, 'professional_profile') and application.professional_profile:
                app_detail.profile_name = application.professional_profile.professional_profile_name
            
            # Check if has analysis
            if hasattr(application, 'analysis') and application.analysis:
                app_detail.has_analysis = True
                app_detail.analysis_id = application.analysis.analyze_application_job_id
                app_detail.total_score = application.analysis.total_score
                app_detail.analysis_date = application.analysis.created_date
            
            # Calculate status and days since application
            app_detail.is_active = application.deleted_date is None
            app_detail.days_since_application = (datetime.utcnow() - application.created_date).days
            
            return app_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting application {application_id}: {e}")
            raise AppException(f"Erro ao buscar candidatura: {str(e)}")
    
    async def get_applications(self, skip: int = 0, limit: int = 100) -> List[ApplicationJobResponse]:
        """Get all applications with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            applications = await self.application_repo.get_all(skip=skip, limit=limit)
            return [ApplicationJobResponse.model_validate(app) for app in applications]
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            raise AppException(f"Erro ao listar candidaturas: {str(e)}")
    
    async def update_application(self, application_id: UUID, application_data: ApplicationJobUpdate) -> ApplicationJobDetail:
        """Update application with business validations"""
        try:
            # Check if application exists
            existing_app = await self.application_repo.get_by_id(application_id)
            if not existing_app:
                raise AppException("Candidatura não encontrada")
            
            # Validate profile if being updated
            if application_data.professional_profile_id:
                profile = await self.profile_repo.get_by_id(application_data.professional_profile_id)
                if not profile or profile.user_id != existing_app.user_id:
                    raise AppException("Perfil profissional não encontrado ou não pertence ao usuário")
            
            # Update application
            updated_app = await self.application_repo.update(application_id, application_data)
            if not updated_app:
                raise AppException("Erro ao atualizar candidatura")
            
            logger.info(f"Application updated successfully: {application_id}")
            return await self.get_application(application_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating application {application_id}: {e}")
            raise AppException(f"Erro ao atualizar candidatura: {str(e)}")
    
    async def withdraw_application(self, application_id: UUID, user_id: UUID) -> bool:
        """Withdraw application (soft delete) with authorization check"""
        try:
            # Check if application exists and belongs to user
            application = await self.application_repo.get_by_id(application_id)
            if not application:
                raise AppException("Candidatura não encontrada")
            
            if application.user_id != user_id:
                raise AppException("Usuário não autorizado a retirar esta candidatura")
            
            # Check if application is already withdrawn
            if application.deleted_date:
                raise AppException("Candidatura já foi retirada")
            
            # Withdraw application
            success = await self.application_repo.soft_delete(application_id)
            if success:
                logger.info(f"Application withdrawn successfully: {application_id} by user {user_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error withdrawing application {application_id}: {e}")
            raise AppException(f"Erro ao retirar candidatura: {str(e)}")
    
    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================
    
    async def get_user_applications(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ApplicationJobSummary]:
        """Get all applications for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            applications = await self.application_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            app_summaries = []
            for app in applications:
                summary = ApplicationJobSummary.model_validate(app)
                
                # Get job and company info
                job = await self.job_repo.get_by_id(app.job_id)
                if job:
                    summary.job_name = job.job_name
                    
                    # Get company info
                    company = await self.job_repo.get_with_details(job.job_id)
                    if company and hasattr(company, 'company') and company.company:
                        summary.company_name = company.company.company_name
                
                # Check for analysis
                # This would require a method to get analysis by application
                # summary.total_score = ... 
                
                app_summaries.append(summary)
            
            return app_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user applications {user_id}: {e}")
            raise AppException(f"Erro ao buscar candidaturas do usuário: {str(e)}")
    
    async def get_user_application_count(self, user_id: UUID) -> int:
        """Get total number of applications for a user"""
        try:
            return await self.application_repo.get_user_application_count(user_id)
        except Exception as e:
            logger.error(f"Error getting user application count: {e}")
            return 0
    
    async def get_user_application_statistics(self, user_id: UUID) -> Dict:
        """Get application statistics for a user"""
        try:
            return await self.application_repo.get_user_statistics(user_id)
        except Exception as e:
            logger.error(f"Error getting user application statistics: {e}")
            raise AppException(f"Erro ao obter estatísticas de candidaturas: {str(e)}")
    
    # =============================================
    # JOB SPECIFIC OPERATIONS
    # =============================================
    
    async def get_job_applications(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[ApplicationJobSummary]:
        """Get all applications for a specific job"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            if limit > 1000:
                limit = 1000
            
            applications = await self.application_repo.get_by_job(job_id, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            app_summaries = []
            for app in applications:
                summary = ApplicationJobSummary.model_validate(app)
                
                # Get user info
                user = await self.user_repo.get_by_id(app.user_id)
                if user:
                    summary.user_name = user.user_name
                
                # Add job info
                summary.job_name = job.job_name
                summary.company_name = None  # Will be filled if company info is needed
                
                app_summaries.append(summary)
            
            return app_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job applications {job_id}: {e}")
            raise AppException(f"Erro ao buscar candidaturas da vaga: {str(e)}")
    
    async def get_job_application_count(self, job_id: UUID) -> int:
        """Get total number of applications for a job"""
        try:
            return await self.application_repo.get_job_application_count(job_id)
        except Exception as e:
            logger.error(f"Error getting job application count: {e}")
            return 0
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_applications(self, filters: ApplicationJobSearchFilters, skip: int = 0, limit: int = 100) -> List[ApplicationJobSummary]:
        """Search applications with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            applications = await self.application_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            app_summaries = []
            for app in applications:
                summary = ApplicationJobSummary.model_validate(app)
                
                # Get user info
                user = await self.user_repo.get_by_id(app.user_id)
                if user:
                    summary.user_name = user.user_name
                
                # Get job info
                job = await self.job_repo.get_by_id(app.job_id)
                if job:
                    summary.job_name = job.job_name
                    
                    # Get company info
                    company_job = await self.job_repo.get_with_details(job.job_id)
                    if company_job and hasattr(company_job, 'company') and company_job.company:
                        summary.company_name = company_job.company.company_name
                
                app_summaries.append(summary)
            
            return app_summaries
            
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            raise AppException(f"Erro ao buscar candidaturas: {str(e)}")
    
    async def get_applications_count(self, filters: Optional[ApplicationJobSearchFilters] = None) -> int:
        """Get total count of applications matching filters"""
        try:
            return await self.application_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting applications count: {e}")
            raise AppException(f"Erro ao contar candidaturas: {str(e)}")
    
    # =============================================
    # BULK OPERATIONS
    # =============================================
    
    async def bulk_apply_to_jobs(self, bulk_data: ApplicationJobBulkCreate) -> ApplicationJobBulkResponse:
        """Apply to multiple jobs at once"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(bulk_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Validate profile exists and belongs to user
            profile = await self.profile_repo.get_by_id(bulk_data.professional_profile_id)
            if not profile or profile.user_id != bulk_data.user_id:
                raise AppException("Perfil profissional não encontrado ou não pertence ao usuário")
            
            created_applications = []
            failed_applications = []
            
            for job_id in bulk_data.job_ids:
                try:
                    # Try to apply to each job
                    application = await self.apply_to_job(
                        user_id=bulk_data.user_id,
                        job_id=job_id,
                        professional_profile_id=bulk_data.professional_profile_id
                    )
                    created_applications.append(application)
                except Exception as e:
                    logger.warning(f"Failed to apply to job {job_id}: {e}")
                    failed_applications.append({
                        "job_id": str(job_id),
                        "error": str(e)
                    })
            
            logger.info(f"Bulk application: {len(created_applications)} created, {len(failed_applications)} failed")
            
            return ApplicationJobBulkResponse(
                created_applications=created_applications,
                failed_applications=failed_applications,
                total_created=len(created_applications),
                total_failed=len(failed_applications)
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error in bulk apply to jobs: {e}")
            raise AppException(f"Erro ao se candidatar em lote: {str(e)}")
    
    # =============================================
    # VALIDATION AND BUSINESS RULES
    # =============================================
    
    async def can_apply_to_job(self, user_id: UUID, job_id: UUID) -> Dict[str, any]:
        """Check if user can apply to job and return reasons if not"""
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return {"can_apply": False, "reasons": ["Usuário não encontrado"]}
            
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                return {"can_apply": False, "reasons": ["Vaga não encontrada"]}
            
            reasons = []
            
            # Check if job is active
            if job.deleted_date:
                reasons.append("Vaga não está mais ativa")
            
            # BR08: Check if already applied
            already_applied = await self.application_repo.check_user_applied(user_id, job_id)
            if already_applied:
                reasons.append("Usuário já se candidatou para esta vaga")
            
            # Check if user has professional profile
            profile = await self.profile_repo.get_user_primary_profile(user_id)
            if not profile:
                reasons.append("Usuário deve ter um perfil profissional")
            
            # Optional: Check if user has curriculum (warning, not blocking per BR07)
            curriculum = await self.curriculum_repo.get_user_active_curriculum(user_id)
            warnings = []
            if not curriculum:
                warnings.append("Recomendado ter um currículo cadastrado")
            
            can_apply = len(reasons) == 0
            
            return {
                "can_apply": can_apply,
                "reasons": reasons,
                "warnings": warnings,
                "job_name": job.job_name,
                "has_profile": profile is not None,
                "has_curriculum": curriculum is not None
            }
            
        except Exception as e:
            logger.error(f"Error checking if can apply to job: {e}")
            return {"can_apply": False, "reasons": ["Erro interno"]}
    
    async def validate_application_data(self, user_id: UUID, job_id: UUID, professional_profile_id: Optional[UUID] = None) -> Dict[str, List[str]]:
        """Validate application data and return validation errors"""
        try:
            errors = {}
            
            # Validate user exists
            if not await self.user_repo.exists(user_id):
                errors.setdefault("user_id", []).append("Usuário não encontrado")
            
            # Validate job exists and is active
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                errors.setdefault("job_id", []).append("Vaga não encontrada")
            elif job.deleted_date:
                errors.setdefault("job_id", []).append("Vaga não está ativa")
            
            # BR08: Check if already applied
            if await self.application_repo.check_user_applied(user_id, job_id):
                errors.setdefault("general", []).append("Usuário já se candidatou para esta vaga")
            
            # Validate profile if provided
            if professional_profile_id:
                profile = await self.profile_repo.get_by_id(professional_profile_id)
                if not profile:
                    errors.setdefault("professional_profile_id", []).append("Perfil profissional não encontrado")
                elif profile.user_id != user_id:
                    errors.setdefault("professional_profile_id", []).append("Perfil não pertence ao usuário")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating application data: {e}")
            return {"general": ["Erro na validação dos dados"]}
    
    # =============================================
    # ANALYTICS AND REPORTING
    # =============================================
    
    async def get_application_statistics(self) -> ApplicationJobStatistics:
        """Get comprehensive application statistics"""
        try:
            # Get basic counts
            total_applications = await self.application_repo.get_count()
            
            # Get statistics by status
            # This would require implementing status tracking in the repository
            
            # Get monthly trends
            monthly_trends = await self.application_repo.get_applications_by_month()
            
            return ApplicationJobStatistics(
                total_applications=total_applications,
                applications_by_month=monthly_trends
                # Add other statistics as needed
            )
            
        except Exception as e:
            logger.error(f"Error getting application statistics: {e}")
            raise AppException(f"Erro ao obter estatísticas de candidaturas: {str(e)}")
    
    async def get_application_trends(self, months: int = 12) -> List[Dict]:
        """Get application trends over time"""
        try:
            return await self.application_repo.get_applications_by_month(months=months)
        except Exception as e:
            logger.error(f"Error getting application trends: {e}")
            raise AppException(f"Erro ao obter tendências de candidaturas: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def application_exists(self, application_id: UUID) -> bool:
        """Check if application exists"""
        try:
            return await self.application_repo.exists(application_id)
        except Exception as e:
            logger.error(f"Error checking if application exists: {e}")
            return False
    
    async def user_has_applied_to_job(self, user_id: UUID, job_id: UUID) -> bool:
        """Check if user has applied to specific job (BR08 validation)"""
        try:
            return await self.application_repo.check_user_applied(user_id, job_id)
        except Exception as e:
            logger.error(f"Error checking if user applied to job: {e}")
            return False