# =============================================
# app/repositories/analyze_application_job_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, Dict
from uuid import UUID
import logging

from app.database.models.analyze_application_job import AnalyzeApplicationJob
from app.database.models.application_job import ApplicationJob
from app.database.models.professional_profile import ProfessionalProfile
from app.database.models.user import User
from app.database.models.job import Job
from app.database.models.company import Company
from app.schemas.analyze_application_job import (
    AnalyzeApplicationJobCreate, 
    AnalyzeApplicationJobUpdate, 
    AnalyzeApplicationJobSearchFilters
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class AnalyzeApplicationJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, analysis_data: AnalyzeApplicationJobCreate, create_user_id: Optional[UUID] = None) -> AnalyzeApplicationJob:
        """Create a new analysis"""
        try:
            db_analysis = AnalyzeApplicationJob(
                professional_profile_id=analysis_data.professional_profile_id,
                user_id=analysis_data.user_id,
                academic_score=analysis_data.academic_score,
                professional_experience_score=analysis_data.professional_experience_score,
                professional_courses_score=analysis_data.professional_courses_score,
                weak_points_score=analysis_data.weak_points_score,
                strong_points_score=analysis_data.strong_points_score,
                total_score=analysis_data.total_score,
                opinion_application_job=analysis_data.opinion_application_job,
                create_user_id=create_user_id
            )
            
            # Calculate total score if not provided
            if db_analysis.total_score == 0.0:
                db_analysis.calculate_total_score()
            
            self.db.add(db_analysis)
            await self.db.commit()
            await self.db.refresh(db_analysis)
            
            logger.info(f"Analysis created successfully: {db_analysis.analyze_application_job_id}")
            return db_analysis
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating analysis: {e}")
            if "professional_profile_id" in str(e).lower():
                raise AppException("Perfil profissional não encontrado")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar análise")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating analysis: {e}")
            raise AppException(f"Erro ao criar análise: {str(e)}")
    
    async def get_by_id(self, analysis_id: UUID) -> Optional[AnalyzeApplicationJob]:
        """Get analysis by ID"""
        try:
            stmt = select(AnalyzeApplicationJob).where(
                and_(AnalyzeApplicationJob.analyze_application_job_id == analysis_id, AnalyzeApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting analysis by ID {analysis_id}: {e}")
            raise AppException(f"Erro ao buscar análise: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJob]:
        """Get all analyses with pagination"""
        try:
            stmt = select(AnalyzeApplicationJob).where(
                AnalyzeApplicationJob.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(AnalyzeApplicationJob.total_score.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all analyses: {e}")
            raise AppException(f"Erro ao listar análises: {str(e)}")
    
    async def update(self, analysis_id: UUID, analysis_data: AnalyzeApplicationJobUpdate) -> Optional[AnalyzeApplicationJob]:
        """Update analysis"""
        try:
            # Get only non-None fields
            update_data = analysis_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(analysis_id)
            
            # Recalculate total score if individual scores are updated
            if any(key in update_data for key in ['academic_score', 'professional_experience_score', 
                                                  'professional_courses_score', 'weak_points_score', 'strong_points_score']):
                # Get current analysis to calculate new total
                current_analysis = await self.get_by_id(analysis_id)
                if current_analysis:
                    # Update scores with new values
                    for key, value in update_data.items():
                        setattr(current_analysis, key, value)
                    # Calculate new total
                    new_total = current_analysis.calculate_total_score()
                    update_data['total_score'] = new_total
            
            stmt = update(AnalyzeApplicationJob).where(
                and_(AnalyzeApplicationJob.analyze_application_job_id == analysis_id, AnalyzeApplicationJob.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(analysis_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao atualizar análise: {str(e)}")
    
    async def soft_delete(self, analysis_id: UUID) -> bool:
        """Soft delete analysis"""
        try:
            from datetime import datetime
            
            stmt = update(AnalyzeApplicationJob).where(
                and_(AnalyzeApplicationJob.analyze_application_job_id == analysis_id, AnalyzeApplicationJob.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Analysis deleted: {analysis_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao deletar análise: {str(e)}")
    
    # =============================================
    # SPECIFIC QUERIES FOR JOB ANALYSIS
    # =============================================
    
    async def get_by_job_ranked(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJob]:
        """Get analyses for a job ranked by score"""
        try:
            stmt = (
                select(AnalyzeApplicationJob)
                .join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(AnalyzeApplicationJob.total_score.desc())
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting ranked analyses for job {job_id}: {e}")
            raise AppException(f"Erro ao buscar ranking da vaga: {str(e)}")
    
    async def get_top_candidates(self, job_id: UUID, limit: int = 10) -> List[AnalyzeApplicationJob]:
        """Get top N candidates for a job"""
        try:
            stmt = (
                select(AnalyzeApplicationJob)
                .join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
                .order_by(AnalyzeApplicationJob.total_score.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting top candidates for job {job_id}: {e}")
            raise AppException(f"Erro ao buscar melhores candidatos: {str(e)}")
    
    async def get_analysis_stats(self, job_id: UUID) -> Dict:
        """Get analysis statistics for a job"""
        try:
            stmt = (
                select(
                    func.count(AnalyzeApplicationJob.analyze_application_job_id).label('total'),
                    func.avg(AnalyzeApplicationJob.total_score).label('avg_score'),
                    func.max(AnalyzeApplicationJob.total_score).label('max_score'),
                    func.min(AnalyzeApplicationJob.total_score).label('min_score'),
                    func.stddev(AnalyzeApplicationJob.total_score).label('std_dev'),
                    func.avg(AnalyzeApplicationJob.academic_score).label('avg_academic'),
                    func.avg(AnalyzeApplicationJob.professional_experience_score).label('avg_experience'),
                    func.avg(AnalyzeApplicationJob.professional_courses_score).label('avg_courses'),
                    func.avg(AnalyzeApplicationJob.strong_points_score).label('avg_strong'),
                    func.avg(AnalyzeApplicationJob.weak_points_score).label('avg_weak')
                )
                .join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                .where(
                    and_(
                        ApplicationJob.job_id == job_id,
                        ApplicationJob.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
            )
            
            result = await self.db.execute(stmt)
            row = result.first()
            
            if not row or row.total == 0:
                return {
                    "total_analyses": 0,
                    "avg_score": None,
                    "max_score": None,
                    "min_score": None,
                    "std_dev": None,
                    "category_averages": {}
                }
            
            return {
                "total_analyses": row.total,
                "avg_score": float(row.avg_score) if row.avg_score else None,
                "max_score": float(row.max_score) if row.max_score else None,
                "min_score": float(row.min_score) if row.min_score else None,
                "std_dev": float(row.std_dev) if row.std_dev else None,
                "category_averages": {
                    "academic": float(row.avg_academic) if row.avg_academic else None,
                    "experience": float(row.avg_experience) if row.avg_experience else None,
                    "courses": float(row.avg_courses) if row.avg_courses else None,
                    "strong_points": float(row.avg_strong) if row.avg_strong else None,
                    "weak_points": float(row.avg_weak) if row.avg_weak else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis stats for job {job_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas da análise: {str(e)}")
    
    # =============================================
    # USER-SPECIFIC QUERIES
    # =============================================
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJob]:
        """Get all analyses for a specific user"""
        try:
            stmt = select(AnalyzeApplicationJob).where(
                and_(
                    AnalyzeApplicationJob.user_id == user_id,
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(AnalyzeApplicationJob.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting analyses by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar análises do usuário: {str(e)}")
    
    async def get_user_best_score(self, user_id: UUID) -> Optional[float]:
        """Get user's best analysis score"""
        try:
            stmt = select(func.max(AnalyzeApplicationJob.total_score)).where(
                and_(
                    AnalyzeApplicationJob.user_id == user_id,
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            result = await self.db.execute(stmt)
            score = result.scalar()
            return float(score) if score is not None else None
            
        except Exception as e:
            logger.error(f"Error getting user best score {user_id}: {e}")
            return None
    
    async def get_user_avg_score(self, user_id: UUID) -> Optional[float]:
        """Get user's average analysis score"""
        try:
            stmt = select(func.avg(AnalyzeApplicationJob.total_score)).where(
                and_(
                    AnalyzeApplicationJob.user_id == user_id,
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            result = await self.db.execute(stmt)
            score = result.scalar()
            return float(score) if score is not None else None
            
        except Exception as e:
            logger.error(f"Error getting user avg score {user_id}: {e}")
            return None
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search(self, filters: AnalyzeApplicationJobSearchFilters, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJob]:
        """Search analyses with filters"""
        try:
            stmt = select(AnalyzeApplicationJob).where(AnalyzeApplicationJob.deleted_date.is_(None))
            
            # Join with related tables if needed
            join_user = filters.user_id is not None
            join_application = filters.job_id is not None or filters.company_id is not None
            join_job = filters.job_id is not None or filters.company_id is not None
            join_company = filters.company_id is not None
            
            if join_application:
                stmt = stmt.join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
            
            if join_job:
                if not join_application:
                    stmt = stmt.join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                stmt = stmt.join(Job, ApplicationJob.job_id == Job.job_id)
            
            if join_company:
                if not join_job:
                    stmt = stmt.join(ApplicationJob, AnalyzeApplicationJob.professional_profile_id == ApplicationJob.professional_profile_id)
                    stmt = stmt.join(Job, ApplicationJob.job_id == Job.job_id)
                stmt = stmt.join(Company, Job.company_id == Company.company_id)
            
            if join_user:
                stmt = stmt.join(User, AnalyzeApplicationJob.user_id == User.user_id)
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(AnalyzeApplicationJob.user_id == filters.user_id)
            
            if filters.professional_profile_id:
                stmt = stmt.where(AnalyzeApplicationJob.professional_profile_id == filters.professional_profile_id)
            
            if filters.job_id:
                stmt = stmt.where(ApplicationJob.job_id == filters.job_id)
            
            if filters.company_id:
                stmt = stmt.where(Company.company_id == filters.company_id)
            
            if filters.min_total_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.total_score >= filters.min_total_score)
            
            if filters.max_total_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.total_score <= filters.max_total_score)
            
            if filters.min_academic_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.academic_score >= filters.min_academic_score)
            
            if filters.min_experience_score is not None:
                stmt = stmt.where(AnalyzeApplicationJob.professional_experience_score >= filters.min_experience_score)
            
            if filters.analyzed_after:
                stmt = stmt.where(AnalyzeApplicationJob.created_date >= filters.analyzed_after)
            
            if filters.analyzed_before:
                stmt = stmt.where(AnalyzeApplicationJob.created_date <= filters.analyzed_before)
            
            if filters.has_opinion is not None:
                if filters.has_opinion:
                    stmt = stmt.where(AnalyzeApplicationJob.opinion_application_job.is_not(None))
                else:
                    stmt = stmt.where(AnalyzeApplicationJob.opinion_application_job.is_(None))
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(AnalyzeApplicationJob.total_score.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching analyses: {e}")
            raise AppException(f"Erro ao buscar análises: {str(e)}")
    
    # =============================================
    # RANKING AND COMPARISON
    # =============================================
    
    async def get_global_ranking(self, limit: int = 100) -> List[Dict]:
        """Get global ranking of all analyses"""
        try:
            stmt = (
                select(
                    AnalyzeApplicationJob.analyze_application_job_id,
                    AnalyzeApplicationJob.user_id,
                    AnalyzeApplicationJob.total_score,
                    User.user_name,
                    User.user_email,
                    AnalyzeApplicationJob.created_date
                )
                .join(User, AnalyzeApplicationJob.user_id == User.user_id)
                .where(
                    and_(
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
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "total_score": float(row.total_score),
                    "analysis_date": row.created_date,
                    "global_position": idx + 1
                }
                for idx, row in enumerate(rows)
            ]
            
        except Exception as e:
            logger.error(f"Error getting global ranking: {e}")
            raise AppException(f"Erro ao obter ranking global: {str(e)}")
    
    async def get_score_distribution(self) -> List[Dict]:
        """Get score distribution for analytics"""
        try:
            # Score ranges: 0-20, 21-40, 41-60, 61-80, 81-100
            ranges = [
                (0, 20, "Muito Baixo"),
                (21, 40, "Baixo"),
                (41, 60, "Médio"),
                (61, 80, "Alto"),
                (81, 100, "Muito Alto")
            ]
            
            distribution = []
            
            for min_score, max_score, category in ranges:
                stmt = select(func.count(AnalyzeApplicationJob.analyze_application_job_id)).where(
                    and_(
                        AnalyzeApplicationJob.total_score >= min_score,
                        AnalyzeApplicationJob.total_score <= max_score,
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
                
                result = await self.db.execute(stmt)
                count = result.scalar() or 0
                
                distribution.append({
                    "range": f"{min_score}-{max_score}",
                    "category": category,
                    "count": count,
                    "min_score": min_score,
                    "max_score": max_score
                })
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting score distribution: {e}")
            raise AppException(f"Erro ao obter distribuição de scores: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, analysis_id: UUID) -> bool:
        """Check if analysis exists"""
        try:
            stmt = select(AnalyzeApplicationJob.analyze_application_job_id).where(
                and_(AnalyzeApplicationJob.analyze_application_job_id == analysis_id, AnalyzeApplicationJob.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if analysis exists {analysis_id}: {e}")
            return False
    
    async def get_by_profile(self, professional_profile_id: UUID) -> Optional[AnalyzeApplicationJob]:
        """Get analysis by professional profile"""
        try:
            stmt = select(AnalyzeApplicationJob).where(
                and_(
                    AnalyzeApplicationJob.professional_profile_id == professional_profile_id,
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            ).order_by(AnalyzeApplicationJob.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting analysis by profile {professional_profile_id}: {e}")
            return None
    
    async def recalculate_score(self, analysis_id: UUID) -> Optional[AnalyzeApplicationJob]:
        """Recalculate total score for an analysis"""
        try:
            analysis = await self.get_by_id(analysis_id)
            if not analysis:
                return None
            
            new_total = analysis.calculate_total_score()
            
            stmt = update(AnalyzeApplicationJob).where(
                AnalyzeApplicationJob.analyze_application_job_id == analysis_id
            ).values(total_score=new_total)
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            return await self.get_by_id(analysis_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recalculating score for analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao recalcular pontuação: {str(e)}")