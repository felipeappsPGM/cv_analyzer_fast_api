# =============================================
# app/repositories/professional_profile_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, Dict
from uuid import UUID
import logging

from app.database.models.professional_profile import ProfessionalProfile
from app.database.models.user import User
from app.database.models.professional_experience import ProfessionalExperience
from app.database.models.academic_background import AcademicBackground
from app.database.models.professional_courses import ProfessionalCourses
from app.database.models.application_job import ApplicationJob
from app.database.models.analyze_application_job import AnalyzeApplicationJob
from app.schemas.professional_profile import (
    ProfessionalProfileCreate, 
    ProfessionalProfileUpdate, 
    ProfessionalProfileSearchFilters
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class ProfessionalProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, profile_data: ProfessionalProfileCreate, create_user_id: Optional[UUID] = None) -> ProfessionalProfile:
        """Create a new professional profile"""
        try:
            db_profile = ProfessionalProfile(
                professional_profile_name=profile_data.professional_profile_name,
                professional_profile_description=profile_data.professional_profile_description,
                user_id=profile_data.user_id,
                academic_background_id=profile_data.academic_background_id,
                professional_experience_id=profile_data.professional_experience_id,
                professional_courses_id=profile_data.professional_courses_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_profile)
            await self.db.commit()
            await self.db.refresh(db_profile)
            
            logger.info(f"Professional profile created successfully: {db_profile.professional_profile_id}")
            return db_profile
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating professional profile: {e}")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar perfil profissional")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating professional profile: {e}")
            raise AppException(f"Erro ao criar perfil profissional: {str(e)}")
    
    async def get_by_id(self, profile_id: UUID) -> Optional[ProfessionalProfile]:
        """Get professional profile by ID"""
        try:
            stmt = select(ProfessionalProfile).where(
                and_(ProfessionalProfile.professional_profile_id == profile_id, ProfessionalProfile.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting professional profile by ID {profile_id}: {e}")
            raise AppException(f"Erro ao buscar perfil profissional: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProfessionalProfile]:
        """Get all professional profiles with pagination"""
        try:
            stmt = select(ProfessionalProfile).where(
                ProfessionalProfile.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(ProfessionalProfile.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all professional profiles: {e}")
            raise AppException(f"Erro ao listar perfis profissionais: {str(e)}")
    
    async def update(self, profile_id: UUID, profile_data: ProfessionalProfileUpdate) -> Optional[ProfessionalProfile]:
        """Update professional profile"""
        try:
            # Get only non-None fields
            update_data = profile_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(profile_id)
            
            stmt = update(ProfessionalProfile).where(
                and_(ProfessionalProfile.professional_profile_id == profile_id, ProfessionalProfile.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(profile_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating professional profile {profile_id}: {e}")
            raise AppException(f"Erro ao atualizar perfil profissional: {str(e)}")
    
    async def soft_delete(self, profile_id: UUID) -> bool:
        """Soft delete professional profile"""
        try:
            from datetime import datetime
            
            stmt = update(ProfessionalProfile).where(
                and_(ProfessionalProfile.professional_profile_id == profile_id, ProfessionalProfile.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Professional profile deleted: {profile_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting professional profile {profile_id}: {e}")
            raise AppException(f"Erro ao deletar perfil profissional: {str(e)}")
    
    # =============================================
    # USER-SPECIFIC QUERIES
    # =============================================
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalProfile]:
        """Get all professional profiles for a specific user"""
        try:
            stmt = select(ProfessionalProfile).where(
                and_(
                    ProfessionalProfile.user_id == user_id,
                    ProfessionalProfile.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(ProfessionalProfile.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting professional profiles by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar perfis profissionais do usuário: {str(e)}")
    
    async def get_user_primary_profile(self, user_id: UUID) -> Optional[ProfessionalProfile]:
        """Get user's primary/most recent professional profile"""
        try:
            stmt = select(ProfessionalProfile).where(
                and_(
                    ProfessionalProfile.user_id == user_id,
                    ProfessionalProfile.deleted_date.is_(None)
                )
            ).order_by(ProfessionalProfile.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user primary profile {user_id}: {e}")
            return None
    
    async def get_with_details(self, profile_id: UUID) -> Optional[ProfessionalProfile]:
        """Get professional profile with all related data"""
        try:
            stmt = (
                select(ProfessionalProfile)
                .options(
                    joinedload(ProfessionalProfile.user),
                    selectinload(ProfessionalProfile.applications),
                    selectinload(ProfessionalProfile.analyses)
                )
                .where(
                    and_(ProfessionalProfile.professional_profile_id == profile_id, ProfessionalProfile.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting professional profile details {profile_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes do perfil profissional: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search(self, filters: ProfessionalProfileSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalProfile]:
        """Search professional profiles with filters"""
        try:
            stmt = select(ProfessionalProfile).where(ProfessionalProfile.deleted_date.is_(None))
            
            # Join with User if needed
            join_user = filters.user_name is not None or filters.user_email is not None
            if join_user:
                stmt = stmt.join(User, ProfessionalProfile.user_id == User.user_id)
            
            # Apply filters
            if filters.professional_profile_name:
                stmt = stmt.where(
                    ProfessionalProfile.professional_profile_name.ilike(f"%{filters.professional_profile_name}%")
                )
            
            if filters.user_id:
                stmt = stmt.where(ProfessionalProfile.user_id == filters.user_id)
            
            if filters.user_name:
                stmt = stmt.where(User.user_name.ilike(f"%{filters.user_name}%"))
            
            if filters.user_email:
                stmt = stmt.where(User.user_email.ilike(f"%{filters.user_email}%"))
            
            if filters.has_academic_background is not None:
                if filters.has_academic_background:
                    stmt = stmt.where(ProfessionalProfile.academic_background_id.is_not(None))
                else:
                    stmt = stmt.where(ProfessionalProfile.academic_background_id.is_(None))
            
            if filters.has_professional_experience is not None:
                if filters.has_professional_experience:
                    stmt = stmt.where(ProfessionalProfile.professional_experience_id.is_not(None))
                else:
                    stmt = stmt.where(ProfessionalProfile.professional_experience_id.is_(None))
            
            if filters.has_professional_courses is not None:
                if filters.has_professional_courses:
                    stmt = stmt.where(ProfessionalProfile.professional_courses_id.is_not(None))
                else:
                    stmt = stmt.where(ProfessionalProfile.professional_courses_id.is_(None))
            
            if filters.created_after:
                stmt = stmt.where(ProfessionalProfile.created_date >= filters.created_after)
            
            if filters.created_before:
                stmt = stmt.where(ProfessionalProfile.created_date <= filters.created_before)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(ProfessionalProfile.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching professional profiles: {e}")
            raise AppException(f"Erro ao buscar perfis profissionais: {str(e)}")
    
    async def get_count(self, filters: Optional[ProfessionalProfileSearchFilters] = None) -> int:
        """Get total count of professional profiles matching filters"""
        try:
            stmt = select(func.count(ProfessionalProfile.professional_profile_id)).where(ProfessionalProfile.deleted_date.is_(None))
            
            if filters:
                # Join with User if needed
                join_user = filters.user_name is not None or filters.user_email is not None
                if join_user:
                    stmt = stmt.join(User, ProfessionalProfile.user_id == User.user_id)
                
                # Apply same filters as in search method
                if filters.professional_profile_name:
                    stmt = stmt.where(
                        ProfessionalProfile.professional_profile_name.ilike(f"%{filters.professional_profile_name}%")
                    )
                
                if filters.user_id:
                    stmt = stmt.where(ProfessionalProfile.user_id == filters.user_id)
                
                if filters.user_name:
                    stmt = stmt.where(User.user_name.ilike(f"%{filters.user_name}%"))
                
                if filters.user_email:
                    stmt = stmt.where(User.user_email.ilike(f"%{filters.user_email}%"))
                
                if filters.has_academic_background is not None:
                    if filters.has_academic_background:
                        stmt = stmt.where(ProfessionalProfile.academic_background_id.is_not(None))
                    else:
                        stmt = stmt.where(ProfessionalProfile.academic_background_id.is_(None))
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting professional profiles count: {e}")
            raise AppException(f"Erro ao contar perfis profissionais: {str(e)}")
    
    # =============================================
    # PROFILE COMPLETENESS AND ANALYTICS
    # =============================================
    
    async def calculate_completeness(self, profile_id: UUID) -> Dict:
        """Calculate profile completeness percentage"""
        try:
            profile = await self.get_by_id(profile_id)
            if not profile:
                return {"completeness_percentage": 0, "missing_items": [], "completed_items": []}
            
            # Define completeness criteria
            criteria = {
                "basic_info": profile.professional_profile_name and profile.professional_profile_description,
                "academic_background": profile.academic_background_id is not None,
                "professional_experience": profile.professional_experience_id is not None,
                "professional_courses": profile.professional_courses_id is not None
            }
            
            completed = sum(1 for complete in criteria.values() if complete)
            total = len(criteria)
            completeness_percentage = (completed / total) * 100
            
            completed_items = [key for key, complete in criteria.items() if complete]
            missing_items = [key for key, complete in criteria.items() if not complete]
            
            return {
                "completeness_percentage": completeness_percentage,
                "completed_items": completed_items,
                "missing_items": missing_items,
                "total_criteria": total,
                "completed_criteria": completed
            }
            
        except Exception as e:
            logger.error(f"Error calculating completeness for profile {profile_id}: {e}")
            return {"completeness_percentage": 0, "missing_items": [], "completed_items": []}
    
    async def get_profiles_by_completeness(self, min_completeness: float, skip: int = 0, limit: int = 100) -> List[ProfessionalProfile]:
        """Get profiles with completeness above threshold"""
        try:
            # This is a simplified version - in production you might want to store completeness in the database
            # For now, we'll get profiles that have most fields filled
            stmt = select(ProfessionalProfile).where(
                and_(
                    ProfessionalProfile.deleted_date.is_(None),
                    ProfessionalProfile.professional_profile_name.is_not(None),
                    ProfessionalProfile.professional_profile_description.is_not(None)
                )
            )
            
            # Add additional filters based on completeness level
            if min_completeness >= 75:  # High completeness
                stmt = stmt.where(
                    and_(
                        ProfessionalProfile.academic_background_id.is_not(None),
                        ProfessionalProfile.professional_experience_id.is_not(None),
                        ProfessionalProfile.professional_courses_id.is_not(None)
                    )
                )
            elif min_completeness >= 50:  # Medium completeness
                stmt = stmt.where(
                    or_(
                        ProfessionalProfile.academic_background_id.is_not(None),
                        ProfessionalProfile.professional_experience_id.is_not(None)
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit).order_by(ProfessionalProfile.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting profiles by completeness: {e}")
            raise AppException(f"Erro ao buscar perfis por completude: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, profile_id: UUID) -> Dict:
        """Get professional profile statistics"""
        try:
            # Get application counts
            total_applications_stmt = select(func.count(ApplicationJob.application_job_id)).where(
                and_(ApplicationJob.professional_profile_id == profile_id, ApplicationJob.deleted_date.is_(None))
            )
            
            # Get analysis counts and average score
            analysis_stats_stmt = select(
                func.count(AnalyzeApplicationJob.analyze_application_job_id).label('total_analyses'),
                func.avg(AnalyzeApplicationJob.total_score).label('avg_score'),
                func.max(AnalyzeApplicationJob.total_score).label('max_score')
            ).where(
                and_(
                    AnalyzeApplicationJob.professional_profile_id == profile_id,
                    AnalyzeApplicationJob.deleted_date.is_(None)
                )
            )
            
            # Execute queries
            total_applications_result = await self.db.execute(total_applications_stmt)
            analysis_stats_result = await self.db.execute(analysis_stats_stmt)
            
            total_applications = total_applications_result.scalar() or 0
            analysis_stats = analysis_stats_result.first()
            
            return {
                "total_applications": total_applications,
                "total_analyses": analysis_stats.total_analyses or 0,
                "avg_score": float(analysis_stats.avg_score) if analysis_stats.avg_score else None,
                "highest_score": float(analysis_stats.max_score) if analysis_stats.max_score else None
            }
            
        except Exception as e:
            logger.error(f"Error getting profile statistics {profile_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas do perfil: {str(e)}")
    
    async def get_profiles_by_performance(self, min_score: float, limit: int = 50) -> List[Dict]:
        """Get top performing profiles by analysis scores"""
        try:
            stmt = (
                select(
                    ProfessionalProfile.professional_profile_id,
                    ProfessionalProfile.professional_profile_name,
                    User.user_name,
                    User.user_email,
                    func.avg(AnalyzeApplicationJob.total_score).label('avg_score'),
                    func.count(AnalyzeApplicationJob.analyze_application_job_id).label('analysis_count')
                )
                .join(User, ProfessionalProfile.user_id == User.user_id)
                .join(AnalyzeApplicationJob, ProfessionalProfile.professional_profile_id == AnalyzeApplicationJob.professional_profile_id)
                .where(
                    and_(
                        ProfessionalProfile.deleted_date.is_(None),
                        User.deleted_date.is_(None),
                        AnalyzeApplicationJob.deleted_date.is_(None)
                    )
                )
                .group_by(
                    ProfessionalProfile.professional_profile_id,
                    ProfessionalProfile.professional_profile_name,
                    User.user_name,
                    User.user_email
                )
                .having(func.avg(AnalyzeApplicationJob.total_score) >= min_score)
                .order_by(func.avg(AnalyzeApplicationJob.total_score).desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "professional_profile_id": row.professional_profile_id,
                    "professional_profile_name": row.professional_profile_name,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "avg_score": float(row.avg_score),
                    "analysis_count": row.analysis_count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting profiles by performance: {e}")
            raise AppException(f"Erro ao buscar perfis por performance: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, profile_id: UUID) -> bool:
        """Check if professional profile exists"""
        try:
            stmt = select(ProfessionalProfile.professional_profile_id).where(
                and_(ProfessionalProfile.professional_profile_id == profile_id, ProfessionalProfile.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if professional profile exists {profile_id}: {e}")
            return False
    
    async def get_user_profile_count(self, user_id: UUID) -> int:
        """Get total number of profiles for a user"""
        try:
            stmt = select(func.count(ProfessionalProfile.professional_profile_id)).where(
                and_(ProfessionalProfile.user_id == user_id, ProfessionalProfile.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user profile count {user_id}: {e}")
            return 0