# =============================================
# app/services/curriculum_service.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Tuple
from uuid import UUID
import logging
import base64
from io import BytesIO
import os

from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.user_repository import UserRepository
from app.schemas.curriculum import (
    CurriculumCreate, CurriculumUpdate, CurriculumResponse, 
    CurriculumDetail, CurriculumSearchFilters, CurriculumUpload,
    CurriculumUploadResponse, CurriculumExtractedData, CurriculumStatistics
)
from app.core.exceptions import AppException, ValidationError

# Criar NotFoundError genérica se não existir
class NotFoundError(AppException):
    """Exception raised when a resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404
        )

logger = logging.getLogger(__name__)

class CurriculumService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.curriculum_repo = CurriculumRepository(db)
        self.user_repo = UserRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_curriculum(
        self, 
        curriculum_data: CurriculumCreate, 
        current_user_id: UUID
    ) -> CurriculumResponse:
        """Create a new curriculum"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(curriculum_data.user_id)
            if not user:
                raise NotFoundError("Usuário não encontrado")
            
            # Check if user can create curriculum for this user_id
            if str(curriculum_data.user_id) != str(current_user_id):
                # Only admin can create curriculum for other users
                current_user = await self.user_repo.get_by_id(current_user_id)
                if not current_user or current_user.user_type != "admin":
                    raise ValidationError("Você só pode criar currículo para si mesmo")
            
            # Check if filename already exists
            if await self.curriculum_repo.filename_exists(curriculum_data.file_name):
                raise ValidationError("Nome do arquivo já está em uso")
            
            # Validate file content
            if curriculum_data.file_base64:
                await self._validate_file_content(curriculum_data.file_base64, curriculum_data.file_name)
            
            # Create curriculum
            curriculum = await self.curriculum_repo.create(curriculum_data, current_user_id)
            
            logger.info(f"Curriculum created: {curriculum.curriculum_id} by user {current_user_id}")
            return CurriculumResponse.model_validate(curriculum)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error creating curriculum: {e}")
            raise AppException(f"Erro ao criar currículo: {str(e)}")
    
    async def get_curriculum(self, curriculum_id: UUID, current_user_id: UUID) -> CurriculumDetail:
        """Get curriculum by ID with access control"""
        try:
            curriculum = await self.curriculum_repo.get_with_details(curriculum_id)
            if not curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            # Check access permissions
            await self._check_curriculum_access(curriculum, current_user_id)
            
            # Get additional details
            file_size = await self.curriculum_repo.get_file_size(curriculum_id)
            
            detail = CurriculumDetail.model_validate(curriculum)
            detail.file_size_bytes = file_size
            detail.download_url = f"/api/v1/curriculum/{curriculum_id}/download"
            
            return detail
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error getting curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao buscar currículo: {str(e)}")
    
    async def update_curriculum(
        self, 
        curriculum_id: UUID, 
        curriculum_data: CurriculumUpdate,
        current_user_id: UUID
    ) -> CurriculumDetail:
        """Update curriculum"""
        try:
            # Check if curriculum exists and user has access
            curriculum = await self.curriculum_repo.get_by_id(curriculum_id)
            if not curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            await self._check_curriculum_access(curriculum, current_user_id)
            
            # Check filename uniqueness if being updated
            if curriculum_data.file_name and curriculum_data.file_name != curriculum.file_name:
                if await self.curriculum_repo.filename_exists(curriculum_data.file_name, curriculum_id):
                    raise ValidationError("Nome do arquivo já está em uso")
            
            # Validate file content if being updated
            if curriculum_data.file_base64:
                file_name = curriculum_data.file_name or curriculum.file_name
                await self._validate_file_content(curriculum_data.file_base64, file_name)
            
            # Update curriculum
            updated_curriculum = await self.curriculum_repo.update(curriculum_id, curriculum_data)
            if not updated_curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            logger.info(f"Curriculum updated: {curriculum_id} by user {current_user_id}")
            return await self.get_curriculum(curriculum_id, current_user_id)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao atualizar currículo: {str(e)}")
    
    async def delete_curriculum(self, curriculum_id: UUID, current_user_id: UUID) -> bool:
        """Soft delete curriculum"""
        try:
            # Check if curriculum exists and user has access
            curriculum = await self.curriculum_repo.get_by_id(curriculum_id)
            if not curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            await self._check_curriculum_access(curriculum, current_user_id)
            
            # Check if curriculum is being used in applications
            # In a full implementation, you would check ApplicationJob table
            # For now, we'll allow deletion
            
            success = await self.curriculum_repo.soft_delete(curriculum_id)
            if success:
                logger.info(f"Curriculum deleted: {curriculum_id} by user {current_user_id}")
            
            return success
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error deleting curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao deletar currículo: {str(e)}")
    
    # =============================================
    # LISTING AND SEARCHING
    # =============================================
    
    async def list_curricula(
        self, 
        filters: Optional[CurriculumSearchFilters] = None,
        skip: int = 0,
        limit: int = 100,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[List[CurriculumResponse], int]:
        """List curricula with filters and pagination"""
        try:
            # Apply user-based filtering for non-admin users
            if filters is None:
                filters = CurriculumSearchFilters()
            
            # Non-admin users can only see their own curricula
            current_user = await self.user_repo.get_by_id(current_user_id)
            if not current_user or current_user.user_type != "admin":
                filters.user_id = current_user_id
            
            # Get curricula and total count
            curricula = await self.curriculum_repo.search(filters, skip, limit)
            total_count = await self.curriculum_repo.get_count(filters)
            
            # Convert to response models
            response_list = [CurriculumResponse.model_validate(c) for c in curricula]
            
            return response_list, total_count
            
        except Exception as e:
            logger.error(f"Error listing curricula: {e}")
            raise AppException(f"Erro ao listar currículos: {str(e)}")
    
    async def get_user_curricula(
        self, 
        user_id: UUID, 
        current_user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CurriculumResponse]:
        """Get all curricula for a specific user"""
        try:
            # Check if user can access this user's curricula
            if str(user_id) != str(current_user_id):
                current_user = await self.user_repo.get_by_id(current_user_id)
                if not current_user or current_user.user_type not in ["admin", "recruiter", "company_owner"]:
                    raise ValidationError("Acesso negado aos currículos deste usuário")
            
            curricula = await self.curriculum_repo.get_by_user(user_id, skip, limit)
            return [CurriculumResponse.model_validate(c) for c in curricula]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting user curricula {user_id}: {e}")
            raise AppException(f"Erro ao buscar currículos do usuário: {str(e)}")
    
    # =============================================
    # FILE OPERATIONS
    # =============================================
    
    async def upload_curriculum(
        self, 
        file_data: bytes,
        file_name: str,
        is_work: bool,
        current_user_id: UUID
    ) -> CurriculumUploadResponse:
        """Upload curriculum file"""
        try:
            # Validate file
            await self._validate_file_upload(file_data, file_name)
            
            # Convert to base64
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            # Create curriculum
            curriculum_create = CurriculumCreate(
                file_base64=file_base64,
                file_name=file_name,
                is_work=is_work,
                user_id=current_user_id
            )
            
            curriculum = await self.create_curriculum(curriculum_create, current_user_id)
            
            return CurriculumUploadResponse(
                curriculum_id=curriculum.curriculum_id,
                file_name=file_name,
                file_size_bytes=len(file_data),
                upload_status="success",
                processing_started=True,
                estimated_processing_time_minutes=2
            )
            
        except (ValidationError, AppException):
            raise
        except Exception as e:
            logger.error(f"Error uploading curriculum: {e}")
            raise AppException(f"Erro ao fazer upload do currículo: {str(e)}")
    
    async def download_curriculum(
        self, 
        curriculum_id: UUID, 
        current_user_id: UUID
    ) -> Tuple[bytes, str, str]:
        """Download curriculum file"""
        try:
            # Check access
            curriculum = await self.curriculum_repo.get_by_id(curriculum_id)
            if not curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            await self._check_curriculum_access(curriculum, current_user_id)
            
            # Get file content
            file_content = await self.curriculum_repo.get_file_content(curriculum_id)
            if not file_content:
                raise NotFoundError("Arquivo não encontrado")
            
            # Determine content type
            content_type = self._get_content_type(curriculum.file_name)
            
            logger.info(f"Curriculum downloaded: {curriculum_id} by user {current_user_id}")
            return file_content, curriculum.file_name, content_type
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error downloading curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao baixar currículo: {str(e)}")
    
    # =============================================
    # PROCESSING OPERATIONS
    # =============================================
    
    async def process_curriculum(
        self, 
        curriculum_id: UUID, 
        current_user_id: UUID
    ) -> Dict:
        """Process curriculum with LLM (basic implementation)"""
        try:
            # Check access
            curriculum = await self.curriculum_repo.get_by_id(curriculum_id)
            if not curriculum:
                raise NotFoundError("Currículo não encontrado")
            
            await self._check_curriculum_access(curriculum, current_user_id)
            
            # Get file content
            file_content = await self.curriculum_repo.get_file_content(curriculum_id)
            if not file_content:
                raise ValidationError("Arquivo não encontrado para processamento")
            
            # Basic text extraction (in a real implementation, you would use LLM service)
            extracted_text = await self._extract_text_from_file(file_content, curriculum.file_name)
            
            # Simulate processing result
            processing_result = {
                "curriculum_id": str(curriculum_id),
                "status": "completed",
                "extracted_text_length": len(extracted_text),
                "confidence_score": 0.85,
                "processing_time_seconds": 5.2,
                "extracted_info": {
                    "has_contact_info": "email" in extracted_text.lower(),
                    "has_experience": "experience" in extracted_text.lower() or "trabalho" in extracted_text.lower(),
                    "has_education": "education" in extracted_text.lower() or "formação" in extracted_text.lower(),
                    "estimated_years_experience": self._estimate_experience_years(extracted_text),
                    "detected_skills": self._extract_basic_skills(extracted_text)
                }
            }
            
            # Mark as processed
            await self.curriculum_repo.mark_as_processed(curriculum_id, processing_result)
            
            logger.info(f"Curriculum processed: {curriculum_id}")
            return processing_result
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error processing curriculum {curriculum_id}: {e}")
            raise AppException(f"Erro ao processar currículo: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, user_id: Optional[UUID] = None) -> CurriculumStatistics:
        """Get curriculum statistics"""
        try:
            stats_data = await self.curriculum_repo.get_statistics(user_id)
            
            return CurriculumStatistics(
                user_id=user_id,
                total_curricula=stats_data.get("total_curricula", 0),
                by_file_type=stats_data.get("by_file_type", {}),
                by_status={"active": stats_data.get("total_curricula", 0)},  # Simplified
                total_file_size_mb=0.0,  # Would calculate from file sizes
                avg_file_size_mb=0.0,
                total_downloads=0,  # Would track downloads
                total_applications=0,  # Would get from applications
                processing_success_rate=100.0,  # Would calculate from processing results
                most_recent_upload=None  # Would get from database
            )
            
        except Exception as e:
            logger.error(f"Error getting curriculum statistics: {e}")
            raise AppException(f"Erro ao obter estatísticas: {str(e)}")
    
    # =============================================
    # PRIVATE HELPER METHODS
    # =============================================
    
    async def _check_curriculum_access(self, curriculum, current_user_id: UUID):
        """Check if user has access to curriculum"""
        current_user = await self.user_repo.get_by_id(current_user_id)
        if not current_user:
            raise ValidationError("Usuário não encontrado")
        
        # Users can access their own curricula
        if str(curriculum.user_id) == str(current_user_id):
            return
        
        # Admin can access all curricula
        if current_user.user_type == "admin":
            return
        
        # Recruiters and company owners can access curricula for recruitment purposes
        if current_user.user_type in ["recruiter", "company_owner"]:
            return
        
        raise ValidationError("Acesso negado a este currículo")
    
    async def _validate_file_content(self, file_base64: str, file_name: str):
        """Validate file content"""
        try:
            # Decode base64
            file_data = base64.b64decode(file_base64)
            await self._validate_file_upload(file_data, file_name)
        except Exception as e:
            raise ValidationError(f"Arquivo inválido: {str(e)}")
    
    async def _validate_file_upload(self, file_data: bytes, file_name: str):
        """Validate file upload"""
        # Check file size (50MB limit)
        if len(file_data) > 50_000_000:
            raise ValidationError("Arquivo muito grande (máximo 50MB)")
        
        if len(file_data) < 100:
            raise ValidationError("Arquivo muito pequeno")
        
        # Check file extension
        valid_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_lower = file_name.lower()
        if not any(file_lower.endswith(ext) for ext in valid_extensions):
            raise ValidationError(f"Tipo de arquivo não suportado. Use: {', '.join(valid_extensions)}")
        
        # Basic file validation without magic library
        # Check for common file signatures (magic numbers)
        if len(file_data) >= 4:
            # PDF signature
            if file_lower.endswith('.pdf') and not file_data[:4] == b'%PDF':
                logger.warning(f"File {file_name} has PDF extension but no PDF signature")
            
            # DOC signature (compound document)
            elif file_lower.endswith('.doc') and not file_data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                logger.warning(f"File {file_name} has DOC extension but no DOC signature")
            
            # DOCX signature (ZIP file)
            elif file_lower.endswith('.docx') and not file_data[:2] == b'PK':
                logger.warning(f"File {file_name} has DOCX extension but no ZIP signature")
        
        # Additional validation: try to decode text files
        if file_lower.endswith('.txt'):
            try:
                file_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    file_data.decode('latin-1')
                except UnicodeDecodeError:
                    raise ValidationError("Arquivo de texto não pode ser decodificado")
    
    def _get_content_type(self, file_name: str) -> str:
        """Get content type from file name"""
        file_lower = file_name.lower()
        if file_lower.endswith('.pdf'):
            return 'application/pdf'
        elif file_lower.endswith('.doc'):
            return 'application/msword'
        elif file_lower.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_lower.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'
    
    async def _extract_text_from_file(self, file_content: bytes, file_name: str) -> str:
        """Basic text extraction from file (placeholder implementation)"""
        file_lower = file_name.lower()
        
        if file_lower.endswith('.txt'):
            try:
                return file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return file_content.decode('latin-1')
                except:
                    return file_content.decode('utf-8', errors='ignore')
        
        # For PDF and DOC files, in a real implementation you would use:
        # - PyPDF2 or pdfplumber for PDF
        # - python-docx for DOCX
        # - Other libraries for DOC
        
        # For now, return a placeholder
        return f"[Extracted text from {file_name}] - Text extraction not fully implemented"
    
    def _estimate_experience_years(self, text: str) -> int:
        """Estimate years of experience from text (basic implementation)"""
        # Very basic implementation - in reality you'd use NLP
        text_lower = text.lower()
        
        # Look for year patterns
        import re
        year_patterns = re.findall(r'\b(19|20)\d{2}\b', text)
        
        if len(year_patterns) >= 2:
            years = [int(year) for year in year_patterns]
            return max(years) - min(years) if len(years) > 1 else 0
        
        return 0
    
    def _extract_basic_skills(self, text: str) -> List[str]:
        """Extract basic skills from text (placeholder implementation)"""
        # Very basic skill detection
        common_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 
            'git', 'docker', 'aws', 'azure', 'kubernetes', 'mongodb',
            'postgresql', 'mysql', 'html', 'css', 'typescript', 'angular',
            'vue', 'spring', 'django', 'flask', 'fastapi'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to 10 skills