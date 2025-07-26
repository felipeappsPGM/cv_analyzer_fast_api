# =============================================
# app/repositories/job_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, Dict
from uuid import UUID
import logging

from app.database.models.job import Job
from app.database.models.company import Company
from app.database.models.application_job import ApplicationJob
from app.database.models.analyze_application_job import AnalyzeApplicationJob
from app.database.models.user import User
from app.schemas.job import JobCreate, JobUpdate, JobSearchFilters
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, job_data: JobCreate, create_user_id: Optional[UUID] = None) -> Job:
        """Create a new job"""
        try:
            db_job = Job(
                job_name=job_data.job_name,
                activities=job_data.activities,
                pre_requisites=job_data.pre_requisites,
                differentials=job_data.differentials,
                code_vacancy_job=job_data.code_vacancy_job,
                company_id=job_data.company_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_job)
            await self.db.commit()
            await self.db.refresh(db_job)
            
            logger.info(f"Job created successfully: {db_job.job_id}")
            return db_job
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating job: {e}")
            if "code_vacancy_job" in str(e).lower():
                raise AppException("Código da vaga já está em uso")
            if "company_id" in str(e).lower():
                raise AppException("Empresa não encontrada")
            raise AppException("Erro de integridade ao criar vaga")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise AppException(f"Erro ao criar vaga: {str(e)}")
    
    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID"""
        try:
            stmt = select(Job).where(
                and_(Job.job_id == job_id, Job.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job by ID {job_id}: {e}")
            raise AppException(f"Erro ao buscar vaga: {str(e)}")
    
    async def get_by_code(self, code_vacancy_job: str) -> Optional[Job]:
        """Get job by vacancy code"""
        try:
            stmt = select(Job).where(
                and_(Job.code_vacancy_job == code_vacancy_job, Job.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job by code {code_vacancy_job}: {e}")
            raise AppException(f"Erro ao buscar vaga por código: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get all active jobs with pagination"""
        try:
            stmt = select(Job).where(
                Job.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(Job.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            raise AppException(f"Erro ao listar vagas: {str(e)}")
    
    async def update(self, job_id: UUID, job_data: JobUpdate) -> Optional[Job]:
        """Update job"""
        try:
            # Get only non-None fields
            update_data = job_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(job_id)
            
            stmt = update(Job).where(
                and_(Job.job_id == job_id, Job.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(job_id)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating job {job_id}: {e}")
            if "code_vacancy_job" in str(e).lower():
                raise AppException("Código da vaga já está em uso")
            raise AppException("Erro de integridade ao atualizar vaga")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job {job_id}: {e}")
            raise AppException(f"Erro ao atualizar vaga: {str(e)}")
    
    async def soft_delete(self, job_id: UUID) -> bool:
        """Soft delete job (close job)"""
        try:
            from datetime import datetime
            
            stmt = update(Job).where(
                and_(Job.job_id == job_id, Job.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Job closed: {job_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error closing job {job_id}: {e}")
            raise AppException(f"Erro ao fechar vaga: {str(e)}")
    
    # =============================================
    # SPECIFIC QUERIES
    # =============================================
    
    async def get_by_company(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get all jobs from a specific company"""
        try:
            stmt = select(Job).where(
                and_(
                    Job.company_id == company_id,
                    Job.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(Job.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting jobs by company {company_id}: {e}")
            raise AppException(f"Erro ao buscar vagas da empresa: {str(e)}")
    
    async def get_active_jobs(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get all active jobs (alias for get_all)"""
        return await self.get_all(skip, limit)
    
    async def search_jobs(self, keywords: str, skip: int = 0, limit: int = 100) -> List[Job]:
        """Search jobs by keywords in name, activities, requirements"""
        try:
            # Create search pattern
            search_pattern = f"%{keywords}%"
            
            stmt = select(Job).where(
                and_(
                    Job.deleted_date.is_(None),
                    or_(
                        Job.job_name.ilike(search_pattern),
                        Job.activities.ilike(search_pattern),
                        Job.pre_requisites.ilike(search_pattern),
                        Job.differentials.ilike(search_pattern)
                    )
                )
            ).offset(skip).limit(limit).order_by(Job.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching jobs with keywords '{keywords}': {e}")
            raise AppException(f"Erro ao buscar vagas: {str(e)}")
    
    async def get_with_details(self, job_id: UUID) -> Optional[Job]:
        """Get job with company and applications details"""
        try:
            stmt = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    selectinload(Job.applications)
                )
                .where(
                    and_(Job.job_id == job_id, Job.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting job details {job_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da vaga: {str(e)}")
    
    async def search(self, filters: JobSearchFilters, skip: int = 0, limit: int = 100) -> List[Job]:
        """Search jobs with advanced filters"""
        try:
            stmt = select(Job).where(Job.deleted_date.is_(None))
            
            # Join with Company if needed
            join_company = False
            if filters.company_name:
                join_company = True
            
            if join_company:
                stmt = stmt.join(Company, Job.company_id == Company.company_id)
            
            # Apply filters
            if filters.job_name:
                stmt = stmt.where(Job.job_name.ilike(f"%{filters.job_name}%"))
            
            if filters.company_id:
                stmt = stmt.where(Job.company_id == filters.company_id)
            
            if filters.company_name:
                stmt = stmt.where(Company.company_name.ilike(f"%{filters.company_name}%"))
            
            if filters.keywords:
                search_pattern = f"%{filters.keywords}%"
                stmt = stmt.where(
                    or_(
                        Job.job_name.ilike(search_pattern),
                        Job.activities.ilike(search_pattern),
                        Job.pre_requisites.ilike(search_pattern),
                        Job.differentials.ilike(search_pattern)
                    )
                )
            
            if filters.code_vacancy_job:
                stmt = stmt.where(Job.code_vacancy_job == filters.code_vacancy_job)
            
            if filters.is_active is not None:
                if filters.is_active:
                    # Already filtered by deleted_date.is_(None)
                    pass
                else:
                    # Include deleted jobs
                    stmt = stmt.filter(Job.deleted_date.is_not(None))
            
            if filters.created_after:
                stmt = stmt.where(Job.created_date >= filters.created_after)
            
            if filters.created_before:
                stmt = stmt.where(Job.created_date <= filters.created_before)
            
            if filters.has_applications is not None:
                if filters.has_applications:
                    stmt = stmt.join(ApplicationJob, Job.job_id == ApplicationJob.job_id).where(
                        ApplicationJob.deleted_date.is_(None)
                    ).distinct()
                else:
                    # Jobs without applications
                    subquery = select(ApplicationJob.job_id).where(
                        ApplicationJob.deleted_date.is_(None)
                    )
                    stmt = stmt.where(Job.job_id.notin_(subquery))
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(Job.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            raise AppException(f"Erro ao buscar vagas: {str(e)}")
    
    async def get_count(self, filters: Optional[JobSearchFilters] = None) -> int:
        """Get total count of jobs matching filters"""
        try:
            stmt = select(func.count(Job.job_id)).where(Job.deleted_date.is_(None))
            
            if filters:
                # Join with Company if needed
                join_company = False
                if filters.company_name:
                    join_company = True
                
                if join_company:
                    stmt = stmt.join(Company, Job.company_id == Company.company_id)
                
                # Apply same filters as in search method
                if filters.job_name:
                    stmt = stmt.where(Job.job_name.ilike(f"%{filters.job_name}%"))
                
                if filters.company_id:
                    stmt = stmt.where(Job.company_id == filters.company_id)
                
                if filters.company_name:
                    stmt = stmt.where(Company.company_name.ilike(f"%{filters.company_name}%"))
                
                if filters.keywords:
                    search_pattern = f"%{filters.keywords}%"
                    stmt = stmt.where(
                        or_(
                            Job.job_name.ilike(search_pattern),
                            Job.activities.ilike(search_pattern),
                            Job.pre_requisites.ilike(search_pattern),
                            Job.differentials.ilike(search_pattern)
                        )
                    )
                
                if filters.has_applications is not None:
                    if filters.has_applications:
                        stmt = stmt.join(ApplicationJob, Job.job_id == ApplicationJob.job_id).where(
                            ApplicationJob.deleted_date.is_(None)
                        )
                    else:
                        subquery = select(ApplicationJob.job_id).where(
                            ApplicationJob.deleted_date.is_(None)
                        )
                        stmt = stmt.where(Job.job_id.notin_(subquery))
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting jobs count: {e}")
            raise AppException(f"Erro ao contar vagas: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, job_id: UUID) -> Dict:
        """Get job statistics"""
        try:
            # Get application counts
            total_applications_stmt = select(func.count(ApplicationJob.application_job_id)).where(
                and_(ApplicationJob.job_id == job_id, ApplicationJob.deleted_date.is_(None))
            )
            
            analyzed_applications_stmt = select(func.count(AnalyzeApplicationJob.analyze_application_job_id)).join(
                ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id
            ).where(
                and_(
                    ApplicationJob.job_id == job_id,
                    ApplicationJob.deleted_date.is_(None),
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            # Get score statistics
            score_stats_stmt = select(
                func.avg(AnalyzeApplicationJob.total_score).label('avg_score'),
                func.max(AnalyzeApplicationJob.total_score).label('max_score'),
                func.min(AnalyzeApplicationJob.total_score).label('min_score')
            ).join(
                ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id
            ).where(
                and_(
                    ApplicationJob.job_id == job_id,
                    ApplicationJob.deleted_date.is_(None),
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            # Execute queries
            total_applications_result = await self.db.execute(total_applications_stmt)
            analyzed_applications_result = await self.db.execute(analyzed_applications_stmt)
            score_stats_result = await self.db.execute(score_stats_stmt)
            
            total_applications = total_applications_result.scalar() or 0
            analyzed_applications = analyzed_applications_result.scalar() or 0
            score_stats = score_stats_result.first()
            
            return {
                "total_applications": total_applications,
                "pending_analysis": total_applications - analyzed_applications,
                "analyzed_applications": analyzed_applications,
                "avg_score": float(score_stats.avg_score) if score_stats.avg_score else None,
                "highest_score": float(score_stats.max_score) if score_stats.max_score else None,
                "lowest_score": float(score_stats.min_score) if score_stats.min_score else None
            }
            
        except Exception as e:
            logger.error(f"Error getting job statistics {job_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas da vaga: {str(e)}")
    
    async def get_top_candidates(self, job_id: UUID, limit: int = 10) -> List[Dict]:
        """Get top candidates for a job by score"""
        try:
            stmt = (
                select(
                    AnalyzeApplicationJob.analyze_application_job_id,
                    AnalyzeApplicationJob.total_score,
                    User.user_id,
                    User.user_name,
                    User.user_email,
                    ApplicationJob.application_job_id,
                    AnalyzeApplicationJob.created_date.label('analysis_date')
                )
                .join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                .join(User, ApplicationJob.user_id == User.user_id)
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None),
                        User.deleted_date.is_(None)
                    )
                )
                .order_by(AnalyzeApplicationJob.total_score.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "analysis_id": row.analyze_application_job_id,
                    "application_id": row.application_job_id,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "total_score": float(row.total_score),
                    "analysis_date": row.analysis_date,
                    "ranking_position": idx + 1
                }
                for idx, row in enumerate(rows)
            ]
            
        except Exception as e:
            logger.error(f"Error getting top candidates for job {job_id}: {e}")
            raise AppException(f"Erro ao obter ranking de candidatos: {str(e)}")
    
    async def get_applications_by_day(self, job_id: UUID, days: int = 30) -> List[Dict]:
        """Get applications count by day for the last N days"""
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                select(
                    func.date(ApplicationJob.created_date).label('date'),
                    func.count(ApplicationJob.application_job_id).label('count')
                )
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        ApplicationJob.created_date >= start_date
                    )
                )
                .group_by(func.date(ApplicationJob.created_date))
                .order_by(func.date(ApplicationJob.created_date))
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "date": row.date.isoformat(),
                    "applications": row.count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting applications by day for job {job_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas de candidaturas: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, job_id: UUID) -> bool:
        """Check if job exists and is active"""
        try:
            stmt = select(Job.job_id).where(
                and_(Job.job_id == job_id, Job.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if job exists {job_id}: {e}")
            return False
    
    async def code_exists(self, code_vacancy_job: str, exclude_job_id: Optional[UUID] = None) -> bool:
        """Check if job code is already in use"""
        try:
            stmt = select(Job.job_id).where(
                and_(Job.code_vacancy_job == code_vacancy_job, Job.deleted_date.is_(None))
            )
            
            if exclude_job_id:
                stmt = stmt.where(Job.job_id != exclude_job_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if job code exists {code_vacancy_job}: {e}")
            return False
    
    async def get_company_jobs_count(self, company_id: UUID) -> int:
        """Get total number of active jobs for a company"""
        try:
            stmt = select(func.count(Job.job_id)).where(
                and_(Job.company_id == company_id, Job.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting company jobs count {company_id}: {e}")
            return 0