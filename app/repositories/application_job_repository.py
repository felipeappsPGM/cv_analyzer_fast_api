# =============================================
# app/repositories/application_job_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, Dict
from uuid import UUID
import logging

from app.database.models.application_job import ApplicationJob
from app.database.models.user import User
from app.database.models.job import Job
from app.database.models.company import Company
from app.database.models.professional_profile import ProfessionalProfile
from app.database.models.analyze_application_job import AnalyzeApplicationJob
from app.schemas.application_job import ApplicationJobCreate, ApplicationJobUpdate, ApplicationJobSearchFilters
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class ApplicationJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, application_data: ApplicationJobCreate, create_user_id: Optional[UUID] = None) -> ApplicationJob:
        """Create a new job application"""
        try:
            db_application = ApplicationJob(
                professional_profile_id=application_data.professional_profile_id,
                job_id=application_data.job_id,
                user_id=application_data.user_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_application)
            await self.db.commit()
            await self.db.refresh(db_application)
            
            logger.info(f"Application created successfully: {db_application.application_job_id}")
            return db_application
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating application: {e}")
            if "uq_user_job_application" in str(e).lower():
                raise AppException("Usuário já se candidatou para esta vaga")
            if "professional_profile_id" in str(e).lower():
                raise AppException("Perfil profissional não encontrado")
            if "job_id" in str(e).lower():
                raise AppException("Vaga não encontrada")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar candidatura")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating application: {e}")
            raise AppException(f"Erro ao criar candidatura: {str(e)}")
    
    async def get_by_id(self, application_id: UUID) -> Optional[ApplicationJob]:
        """Get application by ID"""
        try:
            stmt = select(ApplicationJob).where(
                and_(ApplicationJob.application_job_id == application_id, ApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting application by ID {application_id}: {e}")
            raise AppException(f"Erro ao buscar candidatura: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ApplicationJob]:
        """Get all applications with pagination"""
        try:
            stmt = select(ApplicationJob).where(
                ApplicationJob.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(ApplicationJob.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all applications: {e}")
            raise AppException(f"Erro ao listar candidaturas: {str(e)}")
    
    async def update(self, application_id: UUID, application_data: ApplicationJobUpdate) -> Optional[ApplicationJob]:
        """Update application"""
        try:
            # Get only non-None fields
            update_data = application_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(application_id)
            
            stmt = update(ApplicationJob).where(
                and_(ApplicationJob.application_job_id == application_id, ApplicationJob.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(application_id)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating application {application_id}: {e}")
            raise AppException("Erro de integridade ao atualizar candidatura")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating application {application_id}: {e}")
            raise AppException(f"Erro ao atualizar candidatura: {str(e)}")
    
    async def soft_delete(self, application_id: UUID) -> bool:
        """Soft delete application (withdraw application)"""
        try:
            from datetime import datetime
            
            stmt = update(ApplicationJob).where(
                and_(ApplicationJob.application_job_id == application_id, ApplicationJob.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Application withdrawn: {application_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error withdrawing application {application_id}: {e}")
            raise AppException(f"Erro ao retirar candidatura: {str(e)}")
    
    # =============================================
    # SPECIFIC QUERIES
    # =============================================
    
    async def get_by_job(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[ApplicationJob]:
        """Get all applications for a specific job"""
        try:
            stmt = select(ApplicationJob).where(
                and_(
                    ApplicationJob.job_id == job_id,
                    ApplicationJob.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(ApplicationJob.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting applications by job {job_id}: {e}")
            raise AppException(f"Erro ao buscar candidaturas da vaga: {str(e)}")
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ApplicationJob]:
        """Get all applications from a specific user"""
        try:
            stmt = select(ApplicationJob).where(
                and_(
                    ApplicationJob.user_id == user_id,
                    ApplicationJob.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(ApplicationJob.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting applications by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar candidaturas do usuário: {str(e)}")
    
    async def check_user_applied(self, user_id: UUID, job_id: UUID) -> bool:
        """Check if user has already applied to this job"""
        try:
            stmt = select(ApplicationJob.application_job_id).where(
                and_(
                    ApplicationJob.user_id == user_id,
                    ApplicationJob.job_id == job_id,
                    ApplicationJob.deleted_date.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking if user {user_id} applied to job {job_id}: {e}")
            return False
    
    async def get_with_details(self, application_id: UUID) -> Optional[ApplicationJob]:
        """Get application with user, job, and company details"""
        try:
            stmt = (
                select(ApplicationJob)
                .options(
                    joinedload(ApplicationJob.user),
                    joinedload(ApplicationJob.job).joinedload(Job.company),
                    joinedload(ApplicationJob.professional_profile),
                    selectinload(ApplicationJob.analysis)
                )
                .where(
                    and_(ApplicationJob.application_job_id == application_id, ApplicationJob.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting application details {application_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da candidatura: {str(e)}")
    
    async def search(self, filters: ApplicationJobSearchFilters, skip: int = 0, limit: int = 100) -> List[ApplicationJob]:
        """Search applications with filters"""
        try:
            stmt = select(ApplicationJob).where(ApplicationJob.deleted_date.is_(None))
            
            # Join with related tables if needed
            join_user = filters.user_id is not None
            join_job = filters.job_id is not None or filters.company_id is not None
            join_company = filters.company_id is not None
            join_analysis = filters.has_analysis is not None or filters.min_score is not None or filters.max_score is not None
            
            if join_user:
                stmt = stmt.join(User, ApplicationJob.user_id == User.user_id)
            
            if join_job:
                stmt = stmt.join(Job, ApplicationJob.job_id == Job.job_id)
            
            if join_company:
                if not join_job:
                    stmt = stmt.join(Job, ApplicationJob.job_id == Job.job_id)
                stmt = stmt.join(Company, Job.company_id == Company.company_id)
            
            if join_analysis:
                stmt = stmt.outerjoin(
                    AnalyzeApplicationJob, 
                    ApplicationJob.professional_profile_id == AnalyzeApplicationJob.professional_profile_id
                )
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(ApplicationJob.user_id == filters.user_id)
            
            if filters.job_id:
                stmt = stmt.where(ApplicationJob.job_id == filters.job_id)
            
            if filters.company_id:
                stmt = stmt.where(Company.company_id == filters.company_id)
            
            if filters.professional_profile_id:
                stmt = stmt.where(ApplicationJob.professional_profile_id == filters.professional_profile_id)
            
            if filters.has_analysis is not None:
                if filters.has_analysis:
                    stmt = stmt.where(AnalyzeApplicationJob.analyze_application_job_id.is_not(None))
                else:
                    stmt = stmt.where(AnalyzeApplicationJob.analyze_application_job_id.is_(None))
            
            if filters.min_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.total_score >= filters.min_score)
            
            if filters.max_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.total_score <= filters.max_score)
            
            if filters.applied_after:
                stmt = stmt.where(ApplicationJob.created_date >= filters.applied_after)
            
            if filters.applied_before:
                stmt = stmt.where(ApplicationJob.created_date <= filters.applied_before)
            
            if filters.analyzed_after:
                stmt = stmt.where(AnalyzeApplicationJob.created_date >= filters.analyzed_after)
            
            if filters.analyzed_before:
                stmt = stmt.where(AnalyzeApplicationJob.created_date <= filters.analyzed_before)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(ApplicationJob.created_date.desc())
            
            # Make distinct if we joined with analysis
            if join_analysis:
                stmt = stmt.distinct()
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            raise AppException(f"Erro ao buscar candidaturas: {str(e)}")
    
    async def get_count(self, filters: Optional[ApplicationJobSearchFilters] = None) -> int:
        """Get total count of applications matching filters"""
        try:
            stmt = select(func.count(ApplicationJob.application_job_id.distinct())).where(ApplicationJob.deleted_date.is_(None))
            
            if filters:
                # Apply same filters as in search method but for count
                if filters.user_id:
                    stmt = stmt.where(ApplicationJob.user_id == filters.user_id)
                
                if filters.job_id:
                    stmt = stmt.where(ApplicationJob.job_id == filters.job_id)
                
                if filters.company_id:
                    stmt = stmt.join(Job, ApplicationJob.job_id == Job.job_id).join(
                        Company, Job.company_id == Company.company_id
                    ).where(Company.company_id == filters.company_id)
                
                if filters.has_analysis is not None:
                    stmt = stmt.outerjoin(
                        AnalyzeApplicationJob, 
                        ApplicationJob.professional_profile_id == AnalyzeApplicationJob.professional_profile_id
                    )
                    if filters.has_analysis:
                        stmt = stmt.where(AnalyzeApplicationJob.analyze_application_job_id.is_not(None))
                    else:
                        stmt = stmt.where(AnalyzeApplicationJob.analyze_application_job_id.is_(None))
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting applications count: {e}")
            raise AppException(f"Erro ao contar candidaturas: {str(e)}")
    
    # =============================================
    # RANKING AND ANALYSIS
    # =============================================
    
    async def get_job_ranking(self, job_id: UUID, limit: int = 50) -> List[Dict]:
        """Get ranked applications for a job by score"""
        try:
            stmt = (
                select(
                    ApplicationJob.application_job_id,
                    ApplicationJob.user_id,
                    User.user_name,
                    User.user_email,
                    AnalyzeApplicationJob.total_score,
                    AnalyzeApplicationJob.academic_score,
                    AnalyzeApplicationJob.professional_experience_score,
                    AnalyzeApplicationJob.professional_courses_score,
                    AnalyzeApplicationJob.strong_points_score,
                    AnalyzeApplicationJob.weak_points_score,
                    AnalyzeApplicationJob.created_date.label('analysis_date')
                )
                .join(User, ApplicationJob.user_id == User.user_id)
                .join(
                    AnalyzeApplicationJob, 
                    ApplicationJob.professional_profile_id == AnalyzeApplicationJob.professional_profile_id
                )
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        User.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
                .order_by(AnalyzeApplicationJob.total_score.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "application_job_id": row.application_job_id,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "total_score": float(row.total_score),
                    "academic_score": float(row.academic_score) if row.academic_score else None,
                    "professional_experience_score": float(row.professional_experience_score) if row.professional_experience_score else None,
                    "professional_courses_score": float(row.professional_courses_score) if row.professional_courses_score else None,
                    "strong_points_score": float(row.strong_points_score) if row.strong_points_score else None,
                    "weak_points_score": float(row.weak_points_score) if row.weak_points_score else None,
                    "analysis_date": row.analysis_date,
                    "ranking_position": idx + 1
                }
                for idx, row in enumerate(rows)
            ]
            
        except Exception as e:
            logger.error(f"Error getting job ranking {job_id}: {e}")
            raise AppException(f"Erro ao obter ranking da vaga: {str(e)}")
    
    async def get_pending_analysis(self, limit: int = 100) -> List[ApplicationJob]:
        """Get applications that need analysis"""
        try:
            # Applications without analysis
            subquery = select(AnalyzeApplicationJob.professional_profile_id).where(
                AnalyzeApplicationJob.deleted_date.is_(None)
            )
            
            stmt = select(ApplicationJob).where(
                and_(
                    ApplicationJob.deleted_date.is_(None),
                    ApplicationJob.professional_profile_id.notin_(subquery)
                )
            ).limit(limit).order_by(ApplicationJob.created_date)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting pending analysis applications: {e}")
            raise AppException(f"Erro ao buscar candidaturas para análise: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_user_statistics(self, user_id: UUID) -> Dict:
        """Get user application statistics"""
        try:
            # Total applications
            total_stmt = select(func.count(ApplicationJob.application_job_id)).where(
                and_(ApplicationJob.user_id == user_id, ApplicationJob.deleted_date.is_(None))
            )
            
            # Applications with analysis
            analyzed_stmt = select(func.count(ApplicationJob.application_job_id.distinct())).join(
                AnalyzeApplicationJob, 
                ApplicationJob.professional_profile_id == AnalyzeApplicationJob.professional_profile_id
            ).where(
                and_(
                    ApplicationJob.user_id == user_id,
                    ApplicationJob.deleted_date.is_(None),
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            # Average score
            avg_score_stmt = select(func.avg(AnalyzeApplicationJob.total_score)).join(
                ApplicationJob, 
                AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id
            ).where(
                and_(
                    ApplicationJob.user_id == user_id,
                    ApplicationJob.deleted_date.is_(None),
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            # Execute queries
            total_result = await self.db.execute(total_stmt)
            analyzed_result = await self.db.execute(analyzed_stmt)
            avg_score_result = await self.db.execute(avg_score_stmt)
            
            total_applications = total_result.scalar() or 0
            analyzed_applications = analyzed_result.scalar() or 0
            avg_score = avg_score_result.scalar()
            
            return {
                "total_applications": total_applications,
                "pending_applications": total_applications - analyzed_applications,
                "analyzed_applications": analyzed_applications,
                "avg_score": float(avg_score) if avg_score else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas do usuário: {str(e)}")
    
    async def get_applications_by_month(self, months: int = 12) -> List[Dict]:
        """Get applications count by month for the last N months"""
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=months * 30)
            
            stmt = (
                select(
                    func.extract('year', ApplicationJob.created_date).label('year'),
                    func.extract('month', ApplicationJob.created_date).label('month'),
                    func.count(ApplicationJob.application_job_id).label('count')
                )
                .where(
                    and_(
                        ApplicationJob.deleted_date.is_(None),
                        ApplicationJob.created_date >= start_date
                    )
                )
                .group_by(
                    func.extract('year', ApplicationJob.created_date),
                    func.extract('month', ApplicationJob.created_date)
                )
                .order_by(
                    func.extract('year', ApplicationJob.created_date),
                    func.extract('month', ApplicationJob.created_date)
                )
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "applications": row.count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting applications by month: {e}")
            raise AppException(f"Erro ao obter estatísticas mensais: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, application_id: UUID) -> bool:
        """Check if application exists"""
        try:
            stmt = select(ApplicationJob.application_job_id).where(
                and_(ApplicationJob.application_job_id == application_id, ApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if application exists {application_id}: {e}")
            return False
    
    async def get_job_application_count(self, job_id: UUID) -> int:
        """Get total number of applications for a job"""
        try:
            stmt = select(func.count(ApplicationJob.application_job_id)).where(
                and_(ApplicationJob.job_id == job_id, ApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting job application count {job_id}: {e}")
            return 0
    
    async def get_user_application_count(self, user_id: UUID) -> int:
        """Get total number of applications from a user"""
        try:
            stmt = select(func.count(ApplicationJob.application_job_id)).where(
                and_(ApplicationJob.user_id == user_id, ApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user application count {user_id}: {e}")
            return 0