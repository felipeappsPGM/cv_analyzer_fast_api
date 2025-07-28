# =============================================
# app/repositories/academic_background_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict
from uuid import UUID
import logging
from datetime import date, datetime

from app.database.models.academic_background import AcademicBackground
from app.database.models.user import User
from app.schemas.academic_background import (
    AcademicBackgroundCreate, 
    AcademicBackgroundUpdate, 
    AcademicBackgroundSearchFilters
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class AcademicBackgroundRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, academic_data: AcademicBackgroundCreate, create_user_id: Optional[UUID] = None) -> AcademicBackground:
        """Create a new academic background"""
        try:
            db_academic = AcademicBackground(
                degree_name=academic_data.degree_name,
                degree_type=academic_data.degree_type,
                field_of_study=academic_data.field_of_study,
                institution_name=academic_data.institution_name,
                start_date=academic_data.start_date,
                end_date=academic_data.end_date,
                user_id=academic_data.user_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_academic)
            await self.db.commit()
            await self.db.refresh(db_academic)
            
            logger.info(f"Academic background created successfully: {db_academic.academic_background_id}")
            return db_academic
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating academic background: {e}")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar formação acadêmica")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating academic background: {e}")
            raise AppException(f"Erro ao criar formação acadêmica: {str(e)}")
    
    async def get_by_id(self, academic_id: UUID) -> Optional[AcademicBackground]:
        """Get academic background by ID"""
        try:
            stmt = select(AcademicBackground).where(
                and_(AcademicBackground.academic_background_id == academic_id, AcademicBackground.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting academic background by ID {academic_id}: {e}")
            raise AppException(f"Erro ao buscar formação acadêmica: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AcademicBackground]:
        """Get all academic backgrounds with pagination"""
        try:
            stmt = select(AcademicBackground).where(
                AcademicBackground.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(AcademicBackground.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all academic backgrounds: {e}")
            raise AppException(f"Erro ao listar formações acadêmicas: {str(e)}")
    
    async def update(self, academic_id: UUID, academic_data: AcademicBackgroundUpdate) -> Optional[AcademicBackground]:
        """Update academic background"""
        try:
            # Get only non-None fields
            update_data = academic_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(academic_id)
            
            stmt = update(AcademicBackground).where(
                and_(AcademicBackground.academic_background_id == academic_id, AcademicBackground.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(academic_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating academic background {academic_id}: {e}")
            raise AppException(f"Erro ao atualizar formação acadêmica: {str(e)}")
    
    async def soft_delete(self, academic_id: UUID) -> bool:
        """Soft delete academic background"""
        try:
            stmt = update(AcademicBackground).where(
                and_(AcademicBackground.academic_background_id == academic_id, AcademicBackground.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Academic background deleted: {academic_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting academic background {academic_id}: {e}")
            raise AppException(f"Erro ao deletar formação acadêmica: {str(e)}")
    
    # =============================================
    # USER-SPECIFIC QUERIES
    # =============================================
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AcademicBackground]:
        """Get all academic backgrounds for a specific user"""
        try:
            stmt = select(AcademicBackground).where(
                and_(
                    AcademicBackground.user_id == user_id,
                    AcademicBackground.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(AcademicBackground.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting academic backgrounds by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar formações acadêmicas do usuário: {str(e)}")
    
    async def get_highest_degree(self, user_id: UUID) -> Optional[AcademicBackground]:
        """Get user's highest degree"""
        try:
            # Order by degree level (assuming higher degrees have higher precedence)
            degree_order = {
                "Pós-doutorado": 8,
                "Doutorado": 7,
                "Mestrado": 6,
                "MBA": 5,
                "Especialização": 4,
                "Pós-graduação": 3,
                "Graduação": 2,
                "Tecnólogo": 1,
                "Técnico": 0,
                "Ensino Médio": -1
            }
            
            academic_backgrounds = await self.get_by_user(user_id)
            
            if not academic_backgrounds:
                return None
            
            # Find the highest degree
            highest_degree = max(
                academic_backgrounds,
                key=lambda ab: degree_order.get(ab.degree_type, 0)
            )
            
            return highest_degree
            
        except Exception as e:
            logger.error(f"Error getting highest degree for user {user_id}: {e}")
            return None
    
    async def get_with_details(self, academic_id: UUID) -> Optional[AcademicBackground]:
        """Get academic background with user details"""
        try:
            stmt = (
                select(AcademicBackground)
                .options(joinedload(AcademicBackground.user))
                .where(
                    and_(AcademicBackground.academic_background_id == academic_id, AcademicBackground.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting academic background details {academic_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da formação acadêmica: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search(self, filters: AcademicBackgroundSearchFilters, skip: int = 0, limit: int = 100) -> List[AcademicBackground]:
        """Search academic backgrounds with filters"""
        try:
            stmt = select(AcademicBackground).where(AcademicBackground.deleted_date.is_(None))
            
            # Join with User if needed
            join_user = filters.user_id is not None
            if join_user:
                stmt = stmt.join(User, AcademicBackground.user_id == User.user_id)
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(AcademicBackground.user_id == filters.user_id)
            
            if filters.degree_name:
                stmt = stmt.where(AcademicBackground.degree_name.ilike(f"%{filters.degree_name}%"))
            
            if filters.degree_type:
                stmt = stmt.where(AcademicBackground.degree_type == filters.degree_type)
            
            if filters.field_of_study:
                stmt = stmt.where(AcademicBackground.field_of_study.ilike(f"%{filters.field_of_study}%"))
            
            if filters.institution_name:
                stmt = stmt.where(AcademicBackground.institution_name.ilike(f"%{filters.institution_name}%"))
            
            if filters.status:
                # Calculate status based on dates
                current_date = date.today()
                if filters.status == "Concluído":
                    stmt = stmt.where(
                        and_(
                            AcademicBackground.end_date.is_not(None),
                            AcademicBackground.end_date <= current_date
                        )
                    )
                elif filters.status == "Em Andamento":
                    stmt = stmt.where(
                        or_(
                            AcademicBackground.end_date.is_(None),
                            AcademicBackground.end_date > current_date
                        )
                    )
            
            if filters.is_completed is not None:
                current_date = date.today()
                if filters.is_completed:
                    stmt = stmt.where(
                        and_(
                            AcademicBackground.end_date.is_not(None),
                            AcademicBackground.end_date <= current_date
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            AcademicBackground.end_date.is_(None),
                            AcademicBackground.end_date > current_date
                        )
                    )
            
            if filters.min_duration_months is not None:
                duration_filter = func.extract('days', func.coalesce(AcademicBackground.end_date, func.current_date()) - AcademicBackground.start_date) >= (filters.min_duration_months * 30)
                stmt = stmt.where(duration_filter)
            
            if filters.max_duration_months is not None:
                duration_filter = func.extract('days', func.coalesce(AcademicBackground.end_date, func.current_date()) - AcademicBackground.start_date) <= (filters.max_duration_months * 30)
                stmt = stmt.where(duration_filter)
            
            if filters.start_date_after:
                stmt = stmt.where(AcademicBackground.start_date >= filters.start_date_after)
            
            if filters.start_date_before:
                stmt = stmt.where(AcademicBackground.start_date <= filters.start_date_before)
            
            if filters.graduation_year:
                stmt = stmt.where(func.extract('year', AcademicBackground.end_date) == filters.graduation_year)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(AcademicBackground.start_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching academic backgrounds: {e}")
            raise AppException(f"Erro ao buscar formações acadêmicas: {str(e)}")
    
    async def get_count(self, filters: Optional[AcademicBackgroundSearchFilters] = None) -> int:
        """Get total count of academic backgrounds matching filters"""
        try:
            stmt = select(func.count(AcademicBackground.academic_background_id)).where(AcademicBackground.deleted_date.is_(None))
            
            if filters:
                # Apply same filters as in search method
                if filters.user_id:
                    stmt = stmt.where(AcademicBackground.user_id == filters.user_id)
                
                if filters.degree_name:
                    stmt = stmt.where(AcademicBackground.degree_name.ilike(f"%{filters.degree_name}%"))
                
                if filters.degree_type:
                    stmt = stmt.where(AcademicBackground.degree_type == filters.degree_type)
                
                if filters.field_of_study:
                    stmt = stmt.where(AcademicBackground.field_of_study.ilike(f"%{filters.field_of_study}%"))
                
                if filters.institution_name:
                    stmt = stmt.where(AcademicBackground.institution_name.ilike(f"%{filters.institution_name}%"))
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting academic backgrounds count: {e}")
            raise AppException(f"Erro ao contar formações acadêmicas: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, user_id: UUID) -> Dict:
        """Get academic background statistics for a user"""
        try:
            academic_backgrounds = await self.get_by_user(user_id, limit=1000)
            
            if not academic_backgrounds:
                return {
                    "total_academic_backgrounds": 0,
                    "completed_degrees": 0,
                    "ongoing_degrees": 0,
                    "highest_degree_type": None,
                    "total_study_duration_months": 0,
                    "total_study_duration_years": 0.0,
                    "institutions_attended": [],
                    "fields_of_study": [],
                    "degree_types_completed": []
                }
            
            # Calculate statistics
            total_backgrounds = len(academic_backgrounds)
            completed_degrees = 0
            ongoing_degrees = 0
            total_duration_months = 0
            institutions = set()
            fields = set()
            completed_degree_types = []
            
            current_date = date.today()
            
            for ab in academic_backgrounds:
                institutions.add(ab.institution_name)
                fields.add(ab.field_of_study)
                
                # Check if completed
                if ab.end_date and ab.end_date <= current_date:
                    completed_degrees += 1
                    completed_degree_types.append(ab.degree_type)
                else:
                    ongoing_degrees += 1
                
                # Calculate duration
                end_date = ab.end_date if ab.end_date else current_date
                duration = (end_date - ab.start_date).days
                total_duration_months += int(duration / 30.44)
            
            # Get highest degree
            highest_degree = await self.get_highest_degree(user_id)
            highest_degree_type = highest_degree.degree_type if highest_degree else None
            
            return {
                "total_academic_backgrounds": total_backgrounds,
                "completed_degrees": completed_degrees,
                "ongoing_degrees": ongoing_degrees,
                "highest_degree_type": highest_degree_type,
                "total_study_duration_months": total_duration_months,
                "total_study_duration_years": round(total_duration_months / 12, 1),
                "institutions_attended": list(institutions),
                "fields_of_study": list(fields),
                "degree_types_completed": completed_degree_types
            }
            
        except Exception as e:
            logger.error(f"Error getting academic background statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas de formação acadêmica: {str(e)}")
    
    async def get_degree_progression(self, user_id: UUID) -> List[Dict]:
        """Get academic progression timeline for a user"""
        try:
            academic_backgrounds = await self.get_by_user(user_id, limit=1000)
            
            # Sort by start date
            sorted_backgrounds = sorted(academic_backgrounds, key=lambda x: x.start_date)
            
            progression = []
            for i, ab in enumerate(sorted_backgrounds):
                end_date = ab.end_date if ab.end_date else date.today()
                duration_months = int((end_date - ab.start_date).days / 30.44)
                
                progression.append({
                    "sequence": i + 1,
                    "degree_name": ab.degree_name,
                    "degree_type": ab.degree_type,
                    "field_of_study": ab.field_of_study,
                    "institution_name": ab.institution_name,
                    "start_date": ab.start_date.isoformat(),
                    "end_date": ab.end_date.isoformat() if ab.end_date else None,
                    "duration_months": duration_months,
                    "is_completed": ab.end_date is not None and ab.end_date <= date.today()
                })
            
            return progression
            
        except Exception as e:
            logger.error(f"Error getting degree progression {user_id}: {e}")
            return []
    
    async def get_institutions_ranking(self, limit: int = 10) -> List[Dict]:
        """Get most common institutions"""
        try:
            stmt = (
                select(
                    AcademicBackground.institution_name,
                    func.count(AcademicBackground.academic_background_id).label('student_count')
                )
                .where(AcademicBackground.deleted_date.is_(None))
                .group_by(AcademicBackground.institution_name)
                .order_by(func.count(AcademicBackground.academic_background_id).desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "institution_name": row.institution_name,
                    "student_count": row.student_count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting institutions ranking: {e}")
            return []
    
    async def get_fields_of_study_distribution(self) -> List[Dict]:
        """Get distribution of fields of study"""
        try:
            stmt = (
                select(
                    AcademicBackground.field_of_study,
                    func.count(AcademicBackground.academic_background_id).label('count')
                )
                .where(AcademicBackground.deleted_date.is_(None))
                .group_by(AcademicBackground.field_of_study)
                .order_by(func.count(AcademicBackground.academic_background_id).desc())
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "field_of_study": row.field_of_study,
                    "count": row.count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting fields of study distribution: {e}")
            return []
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, academic_id: UUID) -> bool:
        """Check if academic background exists"""
        try:
            stmt = select(AcademicBackground.academic_background_id).where(
                and_(AcademicBackground.academic_background_id == academic_id, AcademicBackground.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if academic background exists {academic_id}: {e}")
            return False
    
    async def get_user_academic_count(self, user_id: UUID) -> int:
        """Get total number of academic backgrounds for a user"""
        try:
            stmt = select(func.count(AcademicBackground.academic_background_id)).where(
                and_(AcademicBackground.user_id == user_id, AcademicBackground.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user academic count {user_id}: {e}")
            return 0
    
    async def has_degree_type(self, user_id: UUID, degree_type: str) -> bool:
        """Check if user has a specific degree type"""
        try:
            stmt = select(AcademicBackground.academic_background_id).where(
                and_(
                    AcademicBackground.user_id == user_id,
                    AcademicBackground.degree_type == degree_type,
                    AcademicBackground.deleted_date.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking degree type {degree_type} for user {user_id}: {e}")
            return False