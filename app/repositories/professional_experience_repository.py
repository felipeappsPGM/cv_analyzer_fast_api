# =============================================
# app/repositories/professional_experience_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict
from uuid import UUID
import logging
from datetime import date, datetime

from app.database.models.professional_experience import ProfessionalExperience
from app.database.models.user import User
from app.schemas.professional_experience import (
    ProfessionalExperienceCreate, 
    ProfessionalExperienceUpdate, 
    ProfessionalExperienceSearchFilters
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class ProfessionalExperienceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, experience_data: ProfessionalExperienceCreate, create_user_id: Optional[UUID] = None) -> ProfessionalExperience:
        """Create a new professional experience"""
        try:
            db_experience = ProfessionalExperience(
                job_title=experience_data.job_title,
                company_name=experience_data.company_name,
                employment_type=experience_data.employment_type,
                location=experience_data.location,
                start_date=experience_data.start_date,
                end_date=experience_data.end_date,
                is_current=experience_data.is_current,
                user_id=experience_data.user_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_experience)
            await self.db.commit()
            await self.db.refresh(db_experience)
            
            logger.info(f"Professional experience created successfully: {db_experience.professional_experience_id}")
            return db_experience
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating professional experience: {e}")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar experiência profissional")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating professional experience: {e}")
            raise AppException(f"Erro ao criar experiência profissional: {str(e)}")
    
    async def get_by_id(self, experience_id: UUID) -> Optional[ProfessionalExperience]:
        """Get professional experience by ID"""
        try:
            stmt = select(ProfessionalExperience).where(
                and_(ProfessionalExperience.professional_experience_id == experience_id, ProfessionalExperience.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting professional experience by ID {experience_id}: {e}")
            raise AppException(f"Erro ao buscar experiência profissional: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProfessionalExperience]:
        """Get all professional experiences with pagination"""
        try:
            stmt = select(ProfessionalExperience).where(
                ProfessionalExperience.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(ProfessionalExperience.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all professional experiences: {e}")
            raise AppException(f"Erro ao listar experiências profissionais: {str(e)}")
    
    async def update(self, experience_id: UUID, experience_data: ProfessionalExperienceUpdate) -> Optional[ProfessionalExperience]:
        """Update professional experience"""
        try:
            # Get only non-None fields
            update_data = experience_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(experience_id)
            
            stmt = update(ProfessionalExperience).where(
                and_(ProfessionalExperience.professional_experience_id == experience_id, ProfessionalExperience.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(experience_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating professional experience {experience_id}: {e}")
            raise AppException(f"Erro ao atualizar experiência profissional: {str(e)}")
    
    async def soft_delete(self, experience_id: UUID) -> bool:
        """Soft delete professional experience"""
        try:
            stmt = update(ProfessionalExperience).where(
                and_(ProfessionalExperience.professional_experience_id == experience_id, ProfessionalExperience.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Professional experience deleted: {experience_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting professional experience {experience_id}: {e}")
            raise AppException(f"Erro ao deletar experiência profissional: {str(e)}")
    
    # =============================================
    # USER-SPECIFIC QUERIES
    # =============================================
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalExperience]:
        """Get all professional experiences for a specific user"""
        try:
            stmt = select(ProfessionalExperience).where(
                and_(
                    ProfessionalExperience.user_id == user_id,
                    ProfessionalExperience.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(ProfessionalExperience.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting professional experiences by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar experiências profissionais do usuário: {str(e)}")
    
    async def get_current_experience(self, user_id: UUID) -> Optional[ProfessionalExperience]:
        """Get user's current professional experience"""
        try:
            stmt = select(ProfessionalExperience).where(
                and_(
                    ProfessionalExperience.user_id == user_id,
                    ProfessionalExperience.is_current == True,
                    ProfessionalExperience.deleted_date.is_(None)
                )
            ).order_by(ProfessionalExperience.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting current experience for user {user_id}: {e}")
            return None
    
    async def get_with_details(self, experience_id: UUID) -> Optional[ProfessionalExperience]:
        """Get professional experience with user details"""
        try:
            stmt = (
                select(ProfessionalExperience)
                .options(joinedload(ProfessionalExperience.user))
                .where(
                    and_(ProfessionalExperience.professional_experience_id == experience_id, ProfessionalExperience.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting professional experience details {experience_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da experiência profissional: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search(self, filters: ProfessionalExperienceSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalExperience]:
        """Search professional experiences with filters"""
        try:
            stmt = select(ProfessionalExperience).where(ProfessionalExperience.deleted_date.is_(None))
            
            # Join with User if needed
            join_user = filters.user_id is not None
            if join_user:
                stmt = stmt.join(User, ProfessionalExperience.user_id == User.user_id)
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(ProfessionalExperience.user_id == filters.user_id)
            
            if filters.job_title:
                stmt = stmt.where(ProfessionalExperience.job_title.ilike(f"%{filters.job_title}%"))
            
            if filters.company_name:
                stmt = stmt.where(ProfessionalExperience.company_name.ilike(f"%{filters.company_name}%"))
            
            if filters.employment_type:
                stmt = stmt.where(ProfessionalExperience.employment_type == filters.employment_type)
            
            if filters.location:
                stmt = stmt.where(ProfessionalExperience.location.ilike(f"%{filters.location}%"))
            
            if filters.is_current is not None:
                stmt = stmt.where(ProfessionalExperience.is_current == filters.is_current)
            
            if filters.min_duration_months is not None:
                # Calculate duration and filter
                duration_filter = func.extract('days', func.coalesce(ProfessionalExperience.end_date, func.current_date()) - ProfessionalExperience.start_date) >= (filters.min_duration_months * 30)
                stmt = stmt.where(duration_filter)
            
            if filters.max_duration_months is not None:
                duration_filter = func.extract('days', func.coalesce(ProfessionalExperience.end_date, func.current_date()) - ProfessionalExperience.start_date) <= (filters.max_duration_months * 30)
                stmt = stmt.where(duration_filter)
            
            if filters.start_date_after:
                stmt = stmt.where(ProfessionalExperience.start_date >= filters.start_date_after)
            
            if filters.start_date_before:
                stmt = stmt.where(ProfessionalExperience.start_date <= filters.start_date_before)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(ProfessionalExperience.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching professional experiences: {e}")
            raise AppException(f"Erro ao buscar experiências profissionais: {str(e)}")
    
    async def get_count(self, filters: Optional[ProfessionalExperienceSearchFilters] = None) -> int:
        """Get total count of professional experiences matching filters"""
        try:
            stmt = select(func.count(ProfessionalExperience.professional_experience_id)).where(ProfessionalExperience.deleted_date.is_(None))
            
            if filters:
                # Apply same filters as in search method
                if filters.user_id:
                    stmt = stmt.where(ProfessionalExperience.user_id == filters.user_id)
                
                if filters.job_title:
                    stmt = stmt.where(ProfessionalExperience.job_title.ilike(f"%{filters.job_title}%"))
                
                if filters.company_name:
                    stmt = stmt.where(ProfessionalExperience.company_name.ilike(f"%{filters.company_name}%"))
                
                if filters.employment_type:
                    stmt = stmt.where(ProfessionalExperience.employment_type == filters.employment_type)
                
                if filters.is_current is not None:
                    stmt = stmt.where(ProfessionalExperience.is_current == filters.is_current)
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting professional experiences count: {e}")
            raise AppException(f"Erro ao contar experiências profissionais: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, user_id: UUID) -> Dict:
        """Get professional experience statistics for a user"""
        try:
            # Get all experiences for user
            experiences = await self.get_by_user(user_id, limit=1000)
            
            if not experiences:
                return {
                    "total_experiences": 0,
                    "current_positions": 0,
                    "total_duration_months": 0,
                    "avg_duration_months": 0,
                    "companies_worked": [],
                    "job_titles_held": [],
                    "most_common_employment_type": None
                }
            
            # Calculate statistics
            total_experiences = len(experiences)
            current_positions = sum(1 for exp in experiences if exp.is_current)
            
            # Calculate total duration
            total_duration_months = 0
            employment_types = []
            companies = set()
            job_titles = set()
            
            for exp in experiences:
                companies.add(exp.company_name)
                job_titles.add(exp.job_title)
                if exp.employment_type:
                    employment_types.append(exp.employment_type)
                
                # Calculate duration for this experience
                end_date = exp.end_date if exp.end_date else date.today()
                duration = (end_date - exp.start_date).days
                total_duration_months += int(duration / 30.44)  # Average days per month
            
            avg_duration_months = total_duration_months / total_experiences if total_experiences > 0 else 0
            
            # Most common employment type
            most_common_employment_type = None
            if employment_types:
                from collections import Counter
                employment_counter = Counter(employment_types)
                most_common_employment_type = employment_counter.most_common(1)[0][0]
            
            return {
                "total_experiences": total_experiences,
                "current_positions": current_positions,
                "total_duration_months": total_duration_months,
                "total_duration_years": round(total_duration_months / 12, 1),
                "avg_duration_months": round(avg_duration_months, 1),
                "companies_worked": list(companies),
                "job_titles_held": list(job_titles),
                "most_common_employment_type": most_common_employment_type
            }
            
        except Exception as e:
            logger.error(f"Error getting professional experience statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas de experiência profissional: {str(e)}")
    
    async def get_experience_trends(self, user_id: UUID) -> List[Dict]:
        """Get career progression trends for a user"""
        try:
            experiences = await self.get_by_user(user_id, limit=1000)
            
            # Sort by start date
            sorted_experiences = sorted(experiences, key=lambda x: x.start_date)
            
            trends = []
            for i, exp in enumerate(sorted_experiences):
                end_date = exp.end_date if exp.end_date else date.today()
                duration_months = int((end_date - exp.start_date).days / 30.44)
                
                trends.append({
                    "position": i + 1,
                    "job_title": exp.job_title,
                    "company_name": exp.company_name,
                    "start_date": exp.start_date.isoformat(),
                    "end_date": end_date.isoformat() if exp.end_date else None,
                    "duration_months": duration_months,
                    "is_current": exp.is_current,
                    "employment_type": exp.employment_type
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting experience trends {user_id}: {e}")
            return []
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, experience_id: UUID) -> bool:
        """Check if professional experience exists"""
        try:
            stmt = select(ProfessionalExperience.professional_experience_id).where(
                and_(ProfessionalExperience.professional_experience_id == experience_id, ProfessionalExperience.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if professional experience exists {experience_id}: {e}")
            return False
    
    async def get_user_experience_count(self, user_id: UUID) -> int:
        """Get total number of experiences for a user"""
        try:
            stmt = select(func.count(ProfessionalExperience.professional_experience_id)).where(
                and_(ProfessionalExperience.user_id == user_id, ProfessionalExperience.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user experience count {user_id}: {e}")
            return 0
    
    async def get_companies_worked(self, user_id: UUID) -> List[str]:
        """Get list of companies user has worked at"""
        try:
            stmt = select(ProfessionalExperience.company_name.distinct()).where(
                and_(ProfessionalExperience.user_id == user_id, ProfessionalExperience.deleted_date.is_(None))
            ).order_by(ProfessionalExperience.company_name)
            
            result = await self.db.execute(stmt)
            return [company[0] for company in result.all()]
            
        except Exception as e:
            logger.error(f"Error getting companies worked {user_id}: {e}")
            return []
    
    async def get_total_experience_years(self, user_id: UUID) -> float:
        """Calculate total years of experience for a user"""
        try:
            experiences = await self.get_by_user(user_id, limit=1000)
            
            total_days = 0
            for exp in experiences:
                end_date = exp.end_date if exp.end_date else date.today()
                duration_days = (end_date - exp.start_date).days
                total_days += duration_days
            
            # Convert to years (accounting for overlaps would require more complex logic)
            return round(total_days / 365.25, 1)
            
        except Exception as e:
            logger.error(f"Error calculating total experience years {user_id}: {e}")
            return 0.0