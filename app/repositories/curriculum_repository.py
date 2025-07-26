# =============================================
# app/repositories/curriculum_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Tuple
from uuid import UUID
import logging
import base64

from app.database.models.curriculum import Curriculum
from app.database.models.user import User
from app.schemas.curriculum import CurriculumCreate, CurriculumUpdate, CurriculumSearchFilters
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class CurriculumRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, curriculum_data: CurriculumCreate, create_user_id: Optional[UUID] = None) -> Curriculum:
        """Create a new curriculum"""
        try:
            db_curriculum = Curriculum(
                file_base64=curriculum_data.file_base64,
                file_path=curriculum_data.file_path,
                file_name=curriculum_data.file_name,
                is_work=curriculum_data.is_work,
                user_id=curriculum_data.user_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_curriculum)
            await self.db.commit()
            await self.db.refresh(db_curriculum)
            
            logger.info(f"Curriculum created successfully: {db_curriculum.curriculum_id}")
            return db_curriculum
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating curriculum: {e}")
            if "file_name" in str(e).lower():
                raise AppException("Nome do arquivo já está em uso")
            if "user_id" in str(e).lower():
                raise AppException("Usuário não encontrado")
            raise AppException("Erro de integridade ao criar currículo")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating curriculum: {e}")
            raise AppException(f"Erro ao criar currículo: {str(e)}")
    
    async def get_by_id(self, curriculum_id: UUID) -> Optional[Curriculum]:
        """Get curriculum by ID"""
        try:
            stmt = select(Curriculum).where(
                and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting curriculum by ID {curriculum_id}: {e}")
            raise AppException(f"Erro ao buscar currículo: {str(e)}")
    
    async def get_by_filename(self, file_name: str) -> Optional[Curriculum]:
        """Get curriculum by filename"""
        try:
            stmt = select(Curriculum).where(
                and_(Curriculum.file_name == file_name, Curriculum.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting curriculum by filename {file_name}: {e}")
            raise AppException(f"Erro ao buscar currículo por nome: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Curriculum]:
        """Get all curricula with pagination"""
        try:
            stmt = select(Curriculum).where(
                Curriculum.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(Curriculum.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all curricula: {e}")
            raise AppException(f"Erro ao listar currículos: {str(e)}")
    
    async def update(self, curriculum_id: UUID, curriculum_data: CurriculumUpdate) -> Optional[Curriculum]:
        """Update curriculum"""
        try:
            # Get only non-None fields
            update_data = curriculum_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(curriculum_id)
            
            stmt = update(Curriculum).where(
                and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(curriculum_id)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating curriculum {curriculum_id}: {e}")
            if "file_name" in str(e).lower():
                raise AppException("Nome do arquivo já está em uso")
            raise AppException("Erro de integridade ao atualizar currículo")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao atualizar currículo: {str(e)}")
    
    async def soft_delete(self, curriculum_id: UUID) -> bool:
        """Soft delete curriculum"""
        try:
            from datetime import datetime
            
            stmt = update(Curriculum).where(
                and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Curriculum deleted: {curriculum_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao deletar currículo: {str(e)}")
    
    # =============================================
    # USER-SPECIFIC QUERIES
    # =============================================
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Curriculum]:
        """Get all curricula for a specific user"""
        try:
            stmt = select(Curriculum).where(
                and_(
                    Curriculum.user_id == user_id,
                    Curriculum.deleted_date.is_(None)
                )
            ).offset(skip).limit(limit).order_by(Curriculum.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting curricula by user {user_id}: {e}")
            raise AppException(f"Erro ao buscar currículos do usuário: {str(e)}")
    
    async def get_user_active_curriculum(self, user_id: UUID) -> Optional[Curriculum]:
        """Get user's most recent active curriculum"""
        try:
            stmt = select(Curriculum).where(
                and_(
                    Curriculum.user_id == user_id,
                    Curriculum.is_work == True,
                    Curriculum.deleted_date.is_(None)
                )
            ).order_by(Curriculum.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user active curriculum {user_id}: {e}")
            return None
    
    async def get_with_details(self, curriculum_id: UUID) -> Optional[Curriculum]:
        """Get curriculum with user details"""
        try:
            stmt = (
                select(Curriculum)
                .options(joinedload(Curriculum.user))
                .where(
                    and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting curriculum details {curriculum_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes do currículo: {str(e)}")
    
    # =============================================
    # FILE OPERATIONS
    # =============================================
    
    async def get_file_content(self, curriculum_id: UUID) -> Optional[bytes]:
        """Get curriculum file content"""
        try:
            curriculum = await self.get_by_id(curriculum_id)
            if not curriculum:
                return None
            
            if curriculum.file_base64:
                # Decode base64 content
                return base64.b64decode(curriculum.file_base64)
            elif curriculum.file_path:
                # In a real implementation, you would read from file storage
                # For now, return None as file path reading would need file system access
                logger.warning(f"File path reading not implemented for curriculum {curriculum_id}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file content for curriculum {curriculum_id}: {e}")
            return None
    
    async def update_file_content(self, curriculum_id: UUID, file_content: bytes, file_name: Optional[str] = None) -> bool:
        """Update curriculum file content"""
        try:
            # Encode content to base64
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            update_data = {"file_base64": file_base64}
            if file_name:
                update_data["file_name"] = file_name
            
            stmt = update(Curriculum).where(
                and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating file content for curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao atualizar arquivo do currículo: {str(e)}")
    
    async def get_file_size(self, curriculum_id: UUID) -> Optional[int]:
        """Get curriculum file size in bytes"""
        try:
            curriculum = await self.get_by_id(curriculum_id)
            if not curriculum:
                return None
            
            if curriculum.file_base64:
                # Calculate size from base64 (base64 is ~33% larger than original)
                base64_size = len(curriculum.file_base64.encode('utf-8'))
                return int(base64_size * 0.75)  # Approximate original size
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file size for curriculum {curriculum_id}: {e}")
            return None
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search(self, filters: CurriculumSearchFilters, skip: int = 0, limit: int = 100) -> List[Curriculum]:
        """Search curricula with filters"""
        try:
            stmt = select(Curriculum).where(Curriculum.deleted_date.is_(None))
            
            # Join with User if needed
            join_user = filters.user_id is not None
            if join_user:
                stmt = stmt.join(User, Curriculum.user_id == User.user_id)
            
            # Apply filters
            if filters.user_id:
                stmt = stmt.where(Curriculum.user_id == filters.user_id)
            
            if filters.file_name:
                stmt = stmt.where(Curriculum.file_name.ilike(f"%{filters.file_name}%"))
            
            if filters.file_type:
                # Filter by file extension
                extension = f".{filters.file_type.value}"
                stmt = stmt.where(Curriculum.file_name.ilike(f"%{extension}"))
            
            if filters.is_work is not None:
                stmt = stmt.where(Curriculum.is_work == filters.is_work)
            
            if filters.min_file_size is not None:
                # This is approximate since we're storing base64
                stmt = stmt.where(func.length(Curriculum.file_base64) >= filters.min_file_size * 1.33)
            
            if filters.max_file_size is not None:
                # This is approximate since we're storing base64
                stmt = stmt.where(func.length(Curriculum.file_base64) <= filters.max_file_size * 1.33)
            
            if filters.uploaded_after:
                stmt = stmt.where(Curriculum.created_date >= filters.uploaded_after)
            
            if filters.uploaded_before:
                stmt = stmt.where(Curriculum.created_date <= filters.uploaded_before)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(Curriculum.created_date.desc())
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching curricula: {e}")
            raise AppException(f"Erro ao buscar currículos: {str(e)}")
    
    async def get_count(self, filters: Optional[CurriculumSearchFilters] = None) -> int:
        """Get total count of curricula matching filters"""
        try:
            stmt = select(func.count(Curriculum.curriculum_id)).where(Curriculum.deleted_date.is_(None))
            
            if filters:
                # Apply same filters as in search method
                if filters.user_id:
                    stmt = stmt.where(Curriculum.user_id == filters.user_id)
                
                if filters.file_name:
                    stmt = stmt.where(Curriculum.file_name.ilike(f"%{filters.file_name}%"))
                
                if filters.file_type:
                    extension = f".{filters.file_type.value}"
                    stmt = stmt.where(Curriculum.file_name.ilike(f"%{extension}"))
                
                if filters.is_work is not None:
                    stmt = stmt.where(Curriculum.is_work == filters.is_work)
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting curricula count: {e}")
            raise AppException(f"Erro ao contar currículos: {str(e)}")
    
    # =============================================
    # PROCESSING AND STATUS
    # =============================================
    
    async def get_pending_processing(self, limit: int = 100) -> List[Curriculum]:
        """Get curricula that need processing"""
        try:
            # This would typically involve checking a processing status field
            # For now, return recently created curricula that might need processing
            stmt = select(Curriculum).where(
                and_(
                    Curriculum.deleted_date.is_(None),
                    Curriculum.file_base64.is_not(None)  # Has content to process
                )
            ).order_by(Curriculum.created_date.desc()).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting curricula pending processing: {e}")
            raise AppException(f"Erro ao buscar currículos para processamento: {str(e)}")
    
    async def mark_as_processed(self, curriculum_id: UUID, processing_result: Optional[Dict] = None) -> bool:
        """Mark curriculum as processed (this would typically update a status field)"""
        try:
            # In a full implementation, you would have processing status fields
            # For now, we'll just log the action
            logger.info(f"Curriculum {curriculum_id} marked as processed")
            
            # You could add processing metadata here
            # update_data = {"processing_status": "completed", "processing_date": datetime.utcnow()}
            # if processing_result:
            #     update_data["processing_metadata"] = json.dumps(processing_result)
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking curriculum as processed {curriculum_id}: {e}")
            return False
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, user_id: Optional[UUID] = None) -> Dict:
        """Get curriculum statistics"""
        try:
            base_filter = Curriculum.deleted_date.is_(None)
            if user_id:
                base_filter = and_(base_filter, Curriculum.user_id == user_id)
            
            # Total count
            total_stmt = select(func.count(Curriculum.curriculum_id)).where(base_filter)
            
            # Count by work status
            work_stmt = select(func.count(Curriculum.curriculum_id)).where(
                and_(base_filter, Curriculum.is_work == True)
            )
            
            # Count by file type (approximate)
            pdf_stmt = select(func.count(Curriculum.curriculum_id)).where(
                and_(base_filter, Curriculum.file_name.ilike("%.pdf"))
            )
            
            doc_stmt = select(func.count(Curriculum.curriculum_id)).where(
                and_(base_filter, or_(
                    Curriculum.file_name.ilike("%.doc"),
                    Curriculum.file_name.ilike("%.docx")
                ))
            )
            
            # Execute queries
            total_result = await self.db.execute(total_stmt)
            work_result = await self.db.execute(work_stmt)
            pdf_result = await self.db.execute(pdf_stmt)
            doc_result = await self.db.execute(doc_stmt)
            
            total_curricula = total_result.scalar() or 0
            work_curricula = work_result.scalar() or 0
            pdf_count = pdf_result.scalar() or 0
            doc_count = doc_result.scalar() or 0
            
            return {
                "total_curricula": total_curricula,
                "work_curricula": work_curricula,
                "personal_curricula": total_curricula - work_curricula,
                "by_file_type": {
                    "pdf": pdf_count,
                    "doc": doc_count,
                    "others": total_curricula - pdf_count - doc_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting curriculum statistics: {e}")
            raise AppException(f"Erro ao obter estatísticas de currículos: {str(e)}")
    
    async def get_upload_trends(self, days: int = 30) -> List[Dict]:
        """Get curriculum upload trends for the last N days"""
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                select(
                    func.date(Curriculum.created_date).label('date'),
                    func.count(Curriculum.curriculum_id).label('count')
                )
                .where(
                    and_(
                        Curriculum.deleted_date.is_(None),
                        Curriculum.created_date >= start_date
                    )
                )
                .group_by(func.date(Curriculum.created_date))
                .order_by(func.date(Curriculum.created_date))
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "date": row.date.isoformat(),
                    "uploads": row.count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting upload trends: {e}")
            raise AppException(f"Erro ao obter tendências de upload: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, curriculum_id: UUID) -> bool:
        """Check if curriculum exists"""
        try:
            stmt = select(Curriculum.curriculum_id).where(
                and_(Curriculum.curriculum_id == curriculum_id, Curriculum.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if curriculum exists {curriculum_id}: {e}")
            return False
    
    async def filename_exists(self, file_name: str, exclude_curriculum_id: Optional[UUID] = None) -> bool:
        """Check if filename is already in use"""
        try:
            stmt = select(Curriculum.curriculum_id).where(
                and_(Curriculum.file_name == file_name, Curriculum.deleted_date.is_(None))
            )
            
            if exclude_curriculum_id:
                stmt = stmt.where(Curriculum.curriculum_id != exclude_curriculum_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if filename exists {file_name}: {e}")
            return False
    
    async def get_user_curriculum_count(self, user_id: UUID) -> int:
        """Get total number of curricula for a user"""
        try:
            stmt = select(func.count(Curriculum.curriculum_id)).where(
                and_(Curriculum.user_id == user_id, Curriculum.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user curriculum count {user_id}: {e}")
            return 0