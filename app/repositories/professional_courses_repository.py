# =============================================
# app/repositories/professional_courses_repository.py
# =============================================
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
import logging
from datetime import date, datetime

from app.database.models.professional_courses import ProfessionalCourses
from app.schemas.professional_courses import (
    ProfessionalCoursesCreate,
    ProfessionalCoursesUpdate,
    ProfessionalCoursesSearchFilters,
    CourseStatusEnum,
    CourseCategoryEnum
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class ProfessionalCoursesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================

    async def create(self, course_data: ProfessionalCoursesCreate, create_user_id: Optional[UUID] = None) -> ProfessionalCourses:
        """Create a new professional course"""
        try:
            # Convert Pydantic model to dict, excluding None values for optional fields
            course_dict = course_data.model_dump(exclude_unset=True, exclude_none=True)
            
            # Add audit fields
            course_dict['create_user_id'] = create_user_id
            course_dict['created_date'] = datetime.utcnow()
            
            # Create new course instance
            db_course = ProfessionalCourses(**course_dict)
            
            # Add to session and commit
            self.db.add(db_course)
            await self.db.commit()
            await self.db.refresh(db_course)
            
            logger.info(f"Professional course created: {db_course.course_name} for user {db_course.user_id}")
            return db_course
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating professional course: {e}")
            raise AppException(f"Erro ao criar curso profissional: {str(e)}")

    async def get_by_id(self, course_id: UUID) -> Optional[ProfessionalCourses]:
        """Get professional course by ID (active only)"""
        try:
            stmt = select(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.professional_courses_id == course_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting professional course by ID {course_id}: {e}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProfessionalCourses]:
        """Get all professional courses with pagination (active only)"""
        try:
            stmt = select(ProfessionalCourses).where(
                ProfessionalCourses.deleted_date.is_(None)
            ).order_by(desc(ProfessionalCourses.created_date)).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting all professional courses: {e}")
            return []

    async def update(self, course_id: UUID, course_data: ProfessionalCoursesUpdate) -> Optional[ProfessionalCourses]:
        """Update professional course"""
        try:
            # Get update data, excluding None values
            update_dict = course_data.model_dump(exclude_unset=True, exclude_none=True)
            
            if not update_dict:
                # No fields to update
                return await self.get_by_id(course_id)
            
            # Add updated timestamp
            update_dict['updated_date'] = datetime.utcnow()
            
            # Update query
            stmt = update(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.professional_courses_id == course_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            ).values(**update_dict).returning(ProfessionalCourses)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            updated_course = result.scalar_one_or_none()
            if updated_course:
                logger.info(f"Professional course updated: {course_id}")
            
            return updated_course
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating professional course {course_id}: {e}")
            raise AppException(f"Erro ao atualizar curso profissional: {str(e)}")

    async def soft_delete(self, course_id: UUID) -> bool:
        """Soft delete professional course"""
        try:
            stmt = update(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.professional_courses_id == course_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Professional course soft deleted: {course_id}")
            
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error soft deleting professional course {course_id}: {e}")
            return False

    async def exists(self, course_id: UUID) -> bool:
        """Check if professional course exists (and is not deleted)"""
        try:
            stmt = select(ProfessionalCourses.professional_courses_id).where(
                and_(
                    ProfessionalCourses.professional_courses_id == course_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking if professional course exists {course_id}: {e}")
            return False

    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalCourses]:
        """Get all professional courses for a specific user"""
        try:
            stmt = select(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            ).order_by(desc(ProfessionalCourses.start_date)).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting professional courses for user {user_id}: {e}")
            return []

    async def get_user_courses_count(self, user_id: UUID) -> int:
        """Get count of professional courses for a user"""
        try:
            stmt = select(func.count(ProfessionalCourses.professional_courses_id)).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting course count for user {user_id}: {e}")
            return 0

    async def get_user_completed_courses(self, user_id: UUID) -> List[ProfessionalCourses]:
        """Get user's completed courses"""
        try:
            stmt = select(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    ProfessionalCourses.end_date.isnot(None),
                    ProfessionalCourses.end_date <= date.today()
                )
            ).order_by(desc(ProfessionalCourses.end_date))
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting completed courses for user {user_id}: {e}")
            return []

    async def get_user_ongoing_courses(self, user_id: UUID) -> List[ProfessionalCourses]:
        """Get user's ongoing courses"""
        try:
            today = date.today()
            stmt = select(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    or_(
                        ProfessionalCourses.end_date.is_(None),
                        ProfessionalCourses.end_date > today
                    )
                )
            ).order_by(desc(ProfessionalCourses.start_date))
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting ongoing courses for user {user_id}: {e}")
            return []

    async def get_user_courses_with_certificates(self, user_id: UUID) -> List[ProfessionalCourses]:
        """Get user's courses that have certificates"""
        try:
            stmt = select(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    or_(
                        ProfessionalCourses.certification_media_pdf.isnot(None),
                        ProfessionalCourses.certification_media_image.isnot(None)
                    )
                )
            ).order_by(desc(ProfessionalCourses.end_date))
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting courses with certificates for user {user_id}: {e}")
            return []

    # =============================================
    # SEARCH AND FILTERING
    # =============================================

    async def search(self, filters: ProfessionalCoursesSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalCourses]:
        """Search professional courses with filters"""
        try:
            # Build base query
            stmt = select(ProfessionalCourses).where(
                ProfessionalCourses.deleted_date.is_(None)
            )
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(ProfessionalCourses.user_id == filters.user_id)
            
            if filters.course_name:
                stmt = stmt.where(
                    ProfessionalCourses.course_name.icontains(filters.course_name)
                )
            
            if filters.institution_name:
                stmt = stmt.where(
                    ProfessionalCourses.institution_name.icontains(filters.institution_name)
                )
            
            if filters.is_completed is not None:
                if filters.is_completed:
                    stmt = stmt.where(
                        and_(
                            ProfessionalCourses.end_date.isnot(None),
                            ProfessionalCourses.end_date <= date.today()
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            ProfessionalCourses.end_date.is_(None),
                            ProfessionalCourses.end_date > date.today()
                        )
                    )
            
            if filters.has_certificate is not None:
                if filters.has_certificate:
                    stmt = stmt.where(
                        or_(
                            ProfessionalCourses.certification_media_pdf.isnot(None),
                            ProfessionalCourses.certification_media_image.isnot(None)
                        )
                    )
                else:
                    stmt = stmt.where(
                        and_(
                            ProfessionalCourses.certification_media_pdf.is_(None),
                            ProfessionalCourses.certification_media_image.is_(None)
                        )
                    )
            
            if filters.min_duration_hours:
                stmt = stmt.where(
                    ProfessionalCourses.duration_time_hours >= filters.min_duration_hours
                )
            
            if filters.max_duration_hours:
                stmt = stmt.where(
                    ProfessionalCourses.duration_time_hours <= filters.max_duration_hours
                )
            
            if filters.start_date_after:
                stmt = stmt.where(
                    ProfessionalCourses.start_date >= filters.start_date_after
                )
            
            if filters.start_date_before:
                stmt = stmt.where(
                    ProfessionalCourses.start_date <= filters.start_date_before
                )
            
            if filters.completion_year:
                stmt = stmt.where(
                    func.extract('year', ProfessionalCourses.end_date) == filters.completion_year
                )
            
            # Apply pagination and ordering
            stmt = stmt.order_by(desc(ProfessionalCourses.start_date)).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching professional courses: {e}")
            return []

    async def get_count(self, filters: Optional[ProfessionalCoursesSearchFilters] = None) -> int:
        """Get count of professional courses matching filters"""
        try:
            # Build base query
            stmt = select(func.count(ProfessionalCourses.professional_courses_id)).where(
                ProfessionalCourses.deleted_date.is_(None)
            )
            
            # Apply filters if provided
            if filters:
                if filters.user_id:
                    stmt = stmt.where(ProfessionalCourses.user_id == filters.user_id)
                
                if filters.course_name:
                    stmt = stmt.where(
                        ProfessionalCourses.course_name.icontains(filters.course_name)
                    )
                
                if filters.institution_name:
                    stmt = stmt.where(
                        ProfessionalCourses.institution_name.icontains(filters.institution_name)
                    )
                
                if filters.is_completed is not None:
                    if filters.is_completed:
                        stmt = stmt.where(
                            and_(
                                ProfessionalCourses.end_date.isnot(None),
                                ProfessionalCourses.end_date <= date.today()
                            )
                        )
                    else:
                        stmt = stmt.where(
                            or_(
                                ProfessionalCourses.end_date.is_(None),
                                ProfessionalCourses.end_date > date.today()
                            )
                        )
                
                # Apply other filters as needed...
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting courses count: {e}")
            return 0

    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================

    async def get_user_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for user's professional courses"""
        try:
            # Total courses
            total_stmt = select(func.count(ProfessionalCourses.professional_courses_id)).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            )
            total_result = await self.db.execute(total_stmt)
            total_courses = total_result.scalar() or 0
            
            # Completed courses
            completed_stmt = select(func.count(ProfessionalCourses.professional_courses_id)).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    ProfessionalCourses.end_date.isnot(None),
                    ProfessionalCourses.end_date <= date.today()
                )
            )
            completed_result = await self.db.execute(completed_stmt)
            completed_courses = completed_result.scalar() or 0
            
            # Total study hours
            hours_stmt = select(func.sum(ProfessionalCourses.duration_time_hours)).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    ProfessionalCourses.duration_time_hours.isnot(None)
                )
            )
            hours_result = await self.db.execute(hours_stmt)
            total_hours = hours_result.scalar() or 0
            
            # Average course duration
            avg_hours = total_hours / total_courses if total_courses > 0 else 0
            
            # Certificates count
            cert_stmt = select(func.count(ProfessionalCourses.professional_courses_id)).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    or_(
                        ProfessionalCourses.certification_media_pdf.isnot(None),
                        ProfessionalCourses.certification_media_image.isnot(None)
                    )
                )
            )
            cert_result = await self.db.execute(cert_stmt)
            certificates = cert_result.scalar() or 0
            
            # Institutions attended
            inst_stmt = select(func.array_agg(func.distinct(ProfessionalCourses.institution_name))).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            )
            inst_result = await self.db.execute(inst_stmt)
            institutions = inst_result.scalar() or []
            if institutions and institutions[0] is not None:
                institutions = [inst for inst in institutions if inst is not None]
            else:
                institutions = []
            
            return {
                "total_courses": total_courses,
                "completed_courses": completed_courses,
                "ongoing_courses": total_courses - completed_courses,
                "total_study_hours": int(total_hours),
                "avg_course_duration_hours": round(avg_hours, 1) if avg_hours > 0 else None,
                "certificates_earned": certificates,
                "institutions_attended": institutions,
                "completion_rate": round((completed_courses / total_courses) * 100, 1) if total_courses > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user course statistics {user_id}: {e}")
            return {
                "total_courses": 0,
                "completed_courses": 0,
                "ongoing_courses": 0,
                "total_study_hours": 0,
                "avg_course_duration_hours": None,
                "certificates_earned": 0,
                "institutions_attended": [],
                "completion_rate": 0
            }

    async def get_courses_by_year(self, user_id: UUID) -> Dict[int, int]:
        """Get courses count grouped by completion year"""
        try:
            stmt = select(
                func.extract('year', ProfessionalCourses.end_date).label('year'),
                func.count(ProfessionalCourses.professional_courses_id).label('count')
            ).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None),
                    ProfessionalCourses.end_date.isnot(None)
                )
            ).group_by(func.extract('year', ProfessionalCourses.end_date))
            
            result = await self.db.execute(stmt)
            courses_by_year = {int(row.year): row.count for row in result.fetchall()}
            
            return courses_by_year
            
        except Exception as e:
            logger.error(f"Error getting courses by year for user {user_id}: {e}")
            return {}

    async def get_top_institutions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top institutions by number of courses"""
        try:
            stmt = select(
                ProfessionalCourses.institution_name,
                func.count(ProfessionalCourses.professional_courses_id).label('course_count'),
                func.count(func.distinct(ProfessionalCourses.user_id)).label('user_count')
            ).where(
                ProfessionalCourses.deleted_date.is_(None)
            ).group_by(
                ProfessionalCourses.institution_name
            ).order_by(
                desc('course_count')
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            
            return [
                {
                    "institution_name": row.institution_name,
                    "course_count": row.course_count,
                    "user_count": row.user_count
                }
                for row in result.fetchall()
            ]
            
        except Exception as e:
            logger.error(f"Error getting top institutions: {e}")
            return []

    # =============================================
    # BULK OPERATIONS
    # =============================================

    async def bulk_create(self, courses_data: List[ProfessionalCoursesCreate], create_user_id: Optional[UUID] = None) -> List[ProfessionalCourses]:
        """Create multiple professional courses in batch"""
        try:
            created_courses = []
            
            for course_data in courses_data:
                course_dict = course_data.model_dump(exclude_unset=True, exclude_none=True)
                course_dict['create_user_id'] = create_user_id
                course_dict['created_date'] = datetime.utcnow()
                
                db_course = ProfessionalCourses(**course_dict)
                self.db.add(db_course)
                created_courses.append(db_course)
            
            await self.db.commit()
            
            # Refresh all created courses
            for course in created_courses:
                await self.db.refresh(course)
            
            logger.info(f"Bulk created {len(created_courses)} professional courses")
            return created_courses
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk creating professional courses: {e}")
            raise AppException(f"Erro ao criar cursos em lote: {str(e)}")

    async def bulk_delete_by_user(self, user_id: UUID) -> int:
        """Soft delete all courses for a user"""
        try:
            stmt = update(ProfessionalCourses).where(
                and_(
                    ProfessionalCourses.user_id == user_id,
                    ProfessionalCourses.deleted_date.is_(None)
                )
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Bulk deleted {deleted_count} professional courses for user {user_id}")
            
            return deleted_count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk deleting courses for user {user_id}: {e}")
            return 0