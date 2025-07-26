# =============================================
# app/services/job_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from app.repositories.job_repository import JobRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.application_job_repository import ApplicationJobRepository
from app.repositories.analyze_application_job_repository import AnalyzeApplicationJobRepository
from app.schemas.job import (
    JobCreate, 
    JobUpdate, 
    JobResponse, 
    JobDetail, 
    JobSummary,
    JobSearchFilters,
    JobStatistics,
    JobCandidateRanking
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = JobRepository(db)
        self.company_repo = CompanyRepository(db)
        self.application_repo = ApplicationJobRepository(db)
        self.analysis_repo = AnalyzeApplicationJobRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_job(self, job_data: JobCreate, create_user_id: Optional[UUID] = None) -> JobResponse:
        """Create a new job with business validations"""
        try:
            # Validate company exists
            company = await self.company_repo.get_by_id(job_data.company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Validate job code uniqueness
            existing_job = await self.job_repo.get_by_code(job_data.code_vacancy_job)
            if existing_job:
                raise AppException("Código da vaga já está em uso")
            
            # Create job
            job = await self.job_repo.create(job_data, create_user_id)
            
            logger.info(f"Job created successfully: {job.job_name} (ID: {job.job_id})")
            return JobResponse.model_validate(job)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise AppException(f"Erro ao criar vaga: {str(e)}")
    
    async def get_job(self, job_id: UUID) -> JobDetail:
        """Get job by ID with detailed information"""
        try:
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get job statistics
            stats = await self.job_repo.get_statistics(job_id)
            
            # Get company information
            company = await self.company_repo.get_by_id(job.company_id)
            
            # Convert to detail response with additional info
            job_detail = JobDetail.model_validate(job)
            
            # Add company information
            if company:
                job_detail.company_name = company.company_name
                job_detail.company_area = company.area_of_activity
            
            # Add statistics
            job_detail.total_applications = stats.get("total_applications", 0)
            job_detail.pending_applications = stats.get("pending_analysis", 0)
            job_detail.analyzed_applications = stats.get("analyzed_applications", 0)
            job_detail.is_active = job.deleted_date is None
            
            return job_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            raise AppException(f"Erro ao buscar vaga: {str(e)}")
    
    async def get_jobs(self, skip: int = 0, limit: int = 100) -> List[JobResponse]:
        """Get all active jobs with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            jobs = await self.job_repo.get_all(skip=skip, limit=limit)
            return [JobResponse.model_validate(job) for job in jobs]
            
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            raise AppException(f"Erro ao listar vagas: {str(e)}")
    
    async def update_job(self, job_id: UUID, job_data: JobUpdate) -> JobDetail:
        """Update job with business validations"""
        try:
            # Check if job exists
            existing_job = await self.job_repo.get_by_id(job_id)
            if not existing_job:
                raise AppException("Vaga não encontrada")
            
            # Validate job code uniqueness if being updated
            if job_data.code_vacancy_job:
                code_exists = await self.job_repo.code_exists(job_data.code_vacancy_job, exclude_job_id=job_id)
                if code_exists:
                    raise AppException("Código da vaga já está em uso")
            
            # Update job
            updated_job = await self.job_repo.update(job_id, job_data)
            if not updated_job:
                raise AppException("Erro ao atualizar vaga")
            
            logger.info(f"Job updated successfully: {job_id}")
            return await self.get_job(job_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            raise AppException(f"Erro ao atualizar vaga: {str(e)}")
    
    async def close_job(self, job_id: UUID) -> bool:
        """Close job (soft delete) with business validations"""
        try:
            # Check if job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Check if job is already closed
            if job.deleted_date:
                raise AppException("Vaga já está fechada")
            
            # Close job
            success = await self.job_repo.soft_delete(job_id)
            if success:
                logger.info(f"Job closed successfully: {job_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error closing job {job_id}: {e}")
            raise AppException(f"Erro ao fechar vaga: {str(e)}")
    
    # =============================================
    # COMPANY SPECIFIC OPERATIONS
    # =============================================
    
    async def get_company_jobs(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[JobSummary]:
        """Get all jobs for a specific company"""
        try:
            # Validate company exists
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            if limit > 1000:
                limit = 1000
            
            jobs = await self.job_repo.get_by_company(company_id, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            job_summaries = []
            for job in jobs:
                summary = JobSummary.model_validate(job)
                summary.company_name = company.company_name
                
                # Get application count
                app_count = await self.application_repo.get_job_application_count(job.job_id)
                summary.total_applications = app_count
                
                job_summaries.append(summary)
            
            return job_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting company jobs {company_id}: {e}")
            raise AppException(f"Erro ao buscar vagas da empresa: {str(e)}")
    
    async def get_job_details(self, job_id: UUID) -> JobDetail:
        """Get comprehensive job details with all related data"""
        try:
            job = await self.job_repo.get_with_details(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get comprehensive statistics
            stats = await self.get_job_statistics(job_id)
            
            # Convert to detail response
            job_detail = JobDetail.model_validate(job)
            
            # Add company information if available
            if hasattr(job, 'company') and job.company:
                job_detail.company_name = job.company.company_name
                job_detail.company_area = job.company.area_of_activity
            
            # Add statistics
            job_detail.total_applications = stats.total_applications
            job_detail.pending_applications = stats.pending_analysis
            job_detail.analyzed_applications = stats.analyzed_applications
            job_detail.is_active = job.deleted_date is None
            
            return job_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job details {job_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da vaga: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_jobs(self, filters: JobSearchFilters, skip: int = 0, limit: int = 100) -> List[JobSummary]:
        """Search jobs with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            jobs = await self.job_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            job_summaries = []
            for job in jobs:
                summary = JobSummary.model_validate(job)
                
                # Get company name if not already included
                if not summary.company_name and job.company_id:
                    company = await self.company_repo.get_by_id(job.company_id)
                    if company:
                        summary.company_name = company.company_name
                
                # Get application count
                app_count = await self.application_repo.get_job_application_count(job.job_id)
                summary.total_applications = app_count
                
                job_summaries.append(summary)
            
            return job_summaries
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            raise AppException(f"Erro ao buscar vagas: {str(e)}")
    
    async def get_jobs_count(self, filters: Optional[JobSearchFilters] = None) -> int:
        """Get total count of jobs matching filters"""
        try:
            return await self.job_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting jobs count: {e}")
            raise AppException(f"Erro ao contar vagas: {str(e)}")
    
    async def search_jobs_by_keywords(self, keywords: str, skip: int = 0, limit: int = 100) -> List[JobSummary]:
        """Search jobs by keywords in job content"""
        try:
            if limit > 1000:
                limit = 1000
            
            jobs = await self.job_repo.search_jobs(keywords, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            job_summaries = []
            for job in jobs:
                summary = JobSummary.model_validate(job)
                
                # Get company info
                company = await self.company_repo.get_by_id(job.company_id)
                if company:
                    summary.company_name = company.company_name
                
                # Get application count
                app_count = await self.application_repo.get_job_application_count(job.job_id)
                summary.total_applications = app_count
                
                job_summaries.append(summary)
            
            return job_summaries
            
        except Exception as e:
            logger.error(f"Error searching jobs by keywords: {e}")
            raise AppException(f"Erro ao buscar vagas por palavras-chave: {str(e)}")
    
    # =============================================
    # APPLICATION AND RANKING OPERATIONS
    # =============================================
    
    async def get_job_applications(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all applications for a job"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            if limit > 1000:
                limit = 1000
            
            applications = await self.application_repo.get_by_job(job_id, skip=skip, limit=limit)
            
            # Convert to response with additional info
            app_responses = []
            for app in applications:
                app_detail = await self.application_repo.get_with_details(app.application_job_id)
                if app_detail:
                    app_info = {
                        "application_id": app.application_job_id,
                        "user_id": app.user_id,
                        "user_name": app_detail.user.user_name if app_detail.user else None,
                        "user_email": app_detail.user.user_email if app_detail.user else None,
                        "application_date": app.created_date,
                        "has_analysis": app_detail.analysis is not None if hasattr(app_detail, 'analysis') else False
                    }
                    app_responses.append(app_info)
            
            return app_responses
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job applications {job_id}: {e}")
            raise AppException(f"Erro ao buscar candidaturas da vaga: {str(e)}")
    
    async def get_job_ranking(self, job_id: UUID, limit: int = 50) -> List[JobCandidateRanking]:
        """Get ranked candidates for a job"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get ranking from application repository
            ranking_data = await self.application_repo.get_job_ranking(job_id, limit=limit)
            
            # Convert to response format
            rankings = []
            for idx, data in enumerate(ranking_data):
                ranking = JobCandidateRanking(
                    application_id=data["application_job_id"],
                    user_id=data["user_id"],
                    user_name=data["user_name"],
                    user_email=data["user_email"],
                    total_score=data["total_score"],
                    academic_score=data.get("academic_score"),
                    professional_experience_score=data.get("professional_experience_score"),
                    professional_courses_score=data.get("professional_courses_score"),
                    strong_points_score=data.get("strong_points_score"),
                    weak_points_score=data.get("weak_points_score"),
                    analysis_date=data.get("analysis_date"),
                    ranking_position=data["ranking_position"]
                )
                rankings.append(ranking)
            
            return rankings
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job ranking {job_id}: {e}")
            raise AppException(f"Erro ao obter ranking da vaga: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_job_statistics(self, job_id: UUID) -> JobStatistics:
        """Get comprehensive job statistics"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get basic statistics from repository
            stats = await self.job_repo.get_statistics(job_id)
            
            # Get top candidate information
            top_candidates = await self.job_repo.get_top_candidates(job_id, limit=1)
            top_candidate_id = top_candidates[0]["user_id"] if top_candidates else None
            
            # Get applications by day for trends
            applications_by_day = await self.job_repo.get_applications_by_day(job_id, days=30)
            
            return JobStatistics(
                job_id=job_id,
                total_applications=stats.get("total_applications", 0),
                pending_analysis=stats.get("pending_analysis", 0),
                analyzed_applications=stats.get("analyzed_applications", 0),
                avg_score=stats.get("avg_score"),
                highest_score=stats.get("highest_score"),
                lowest_score=stats.get("lowest_score"),
                top_candidate_id=top_candidate_id,
                applications_by_day=applications_by_day
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job statistics {job_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas da vaga: {str(e)}")
    
    async def get_applications_trends(self, job_id: UUID, days: int = 30) -> List[Dict]:
        """Get application trends for a job"""
        try:
            return await self.job_repo.get_applications_by_day(job_id, days=days)
        except Exception as e:
            logger.error(f"Error getting applications trends: {e}")
            raise AppException(f"Erro ao obter tendências de candidaturas: {str(e)}")
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def validate_job_code_availability(self, code_vacancy_job: str, exclude_job_id: Optional[UUID] = None) -> bool:
        """Check if job code is available for use"""
        try:
            exists = await self.job_repo.code_exists(code_vacancy_job, exclude_job_id)
            return not exists
        except Exception as e:
            logger.error(f"Error validating job code availability: {e}")
            return False
    
    async def job_exists(self, job_id: UUID) -> bool:
        """Check if job exists and is active"""
        try:
            return await self.job_repo.exists(job_id)
        except Exception as e:
            logger.error(f"Error checking if job exists: {e}")
            return False
    
    async def job_is_active(self, job_id: UUID) -> bool:
        """Check if job is active (not closed)"""
        try:
            job = await self.job_repo.get_by_id(job_id)
            return job is not None and job.deleted_date is None
        except Exception as e:
            logger.error(f"Error checking if job is active: {e}")
            return False
    
    # =============================================
    # BUSINESS RULES VALIDATION
    # =============================================
    
    async def can_close_job(self, job_id: UUID) -> Dict[str, any]:
        """Check if job can be closed and return reasons if not"""
        try:
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                return {"can_close": False, "reasons": ["Vaga não encontrada"]}
            
            if job.deleted_date:
                return {"can_close": False, "reasons": ["Vaga já está fechada"]}
            
            reasons = []
            
            # Check for pending analyses
            pending_count = await self.application_repo.get_count()  # This would need filtering by job
            if pending_count > 0:
                reasons.append(f"Há {pending_count} análise(s) pendente(s)")
            
            # Add other business rules here
            
            can_close = len(reasons) == 0
            
            return {
                "can_close": can_close,
                "reasons": reasons,
                "job_name": job.job_name,
                "total_applications": await self.application_repo.get_job_application_count(job_id)
            }
            
        except Exception as e:
            logger.error(f"Error checking if job can be closed: {e}")
            return {"can_close": False, "reasons": ["Erro interno"]}
    
    async def validate_job_data(self, job_data: JobCreate) -> Dict[str, List[str]]:
        """Validate job data and return validation errors"""
        try:
            errors = {}
            
            # Validate job code
            if await self.job_repo.code_exists(job_data.code_vacancy_job):
                errors.setdefault("code_vacancy_job", []).append("Código da vaga já está em uso")
            
            # Validate company exists
            if not await self.company_repo.exists(job_data.company_id):
                errors.setdefault("company_id", []).append("Empresa não encontrada")
            
            # Add other business validations here
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating job data: {e}")
            return {"general": ["Erro na validação dos dados"]}
    
    # =============================================
    # RECOMMENDATION ENGINE
    # =============================================
    
    async def get_similar_jobs(self, job_id: UUID, limit: int = 5) -> List[JobSummary]:
        """Get jobs similar to the given job (simplified implementation)"""
        try:
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Simple similarity based on company and job name keywords
            # In a real implementation, you would use more sophisticated matching
            filters = JobSearchFilters(
                company_id=job.company_id,
                is_active=True
            )
            
            similar_jobs = await self.job_repo.search(filters, skip=0, limit=limit + 1)
            
            # Remove the original job from results
            similar_jobs = [j for j in similar_jobs if j.job_id != job_id][:limit]
            
            # Convert to summary
            summaries = []
            for similar_job in similar_jobs:
                summary = JobSummary.model_validate(similar_job)
                
                # Get company info
                company = await self.company_repo.get_by_id(similar_job.company_id)
                if company:
                    summary.company_name = company.company_name
                
                summaries.append(summary)
            
            return summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting similar jobs: {e}")
            return []