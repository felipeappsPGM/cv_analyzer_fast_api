# =============================================
# app/api/v1/endpoints/curriculum.py
# =============================================
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from app.config.database import get_db
from app.services.curriculum_service import CurriculumService
from app.schemas.curriculum import (
    CurriculumCreate, CurriculumUpdate, CurriculumResponse, 
    CurriculumDetail, CurriculumSearchFilters, CurriculumUploadResponse,
    CurriculumStatistics, FileTypeEnum, CurriculumStatusEnum
)
from app.schemas.user import UserResponse
from app.core.exceptions import AppException

# Criar exceções genéricas se não existirem
class NotFoundError(AppException):
    """Exception raised when a resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404
        )

class ValidationError(AppException):
    """Exception raised when validation fails"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            message=message,
            status_code=400
        )
from app.api.v1.endpoints.auth import get_current_user

# =============================================
# ROUTER AND DEPENDENCIES
# =============================================
router = APIRouter()
logger = logging.getLogger(__name__)

async def get_curriculum_service(db: AsyncSession = Depends(get_db)) -> CurriculumService:
    return CurriculumService(db)

# =============================================
# CURRICULUM CRUD ENDPOINTS
# =============================================

@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
async def create_curriculum(
    curriculum_data: CurriculumCreate,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Create a new curriculum
    
    - **file_name**: Name of the curriculum file
    - **file_base64**: File content encoded in base64 (optional)
    - **file_path**: Path to file in storage (optional)
    - **is_work**: Whether this is a professional curriculum
    - **user_id**: ID of the user who owns this curriculum
    
    Only the curriculum owner or admin can create curricula.
    """
    try:
        return await service.create_curriculum(curriculum_data, current_user.user_id)
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/upload", response_model=CurriculumUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_curriculum(
    file: UploadFile = File(...),
    is_work: bool = Form(True),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Upload a curriculum file
    
    - **file**: Curriculum file (PDF, DOC, DOCX, TXT)
    - **is_work**: Whether this is a professional curriculum
    
    Maximum file size: 50MB
    Supported formats: PDF, DOC, DOCX, TXT
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Nome do arquivo é obrigatório"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload curriculum
        result = await service.upload_curriculum(
            file_data=file_content,
            file_name=file.filename,
            is_work=is_work,
            current_user_id=current_user.user_id
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=dict)
async def list_curricula(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    file_name: Optional[str] = Query(None, description="Filter by file name"),
    file_type: Optional[FileTypeEnum] = Query(None, description="Filter by file type"),
    is_work: Optional[bool] = Query(None, description="Filter by work curriculum"),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    List curricula with optional filters
    
    Returns paginated list of curricula. Non-admin users can only see their own curricula.
    
    **Filters:**
    - **user_id**: Filter by user (admin only)
    - **file_name**: Search in file names
    - **file_type**: Filter by file type (pdf, doc, docx, txt)
    - **is_work**: Filter professional curricula
    """
    try:
        # Build filters
        filters = CurriculumSearchFilters(
            user_id=user_id,
            file_name=file_name,
            file_type=file_type,
            is_work=is_work
        )
        
        curricula, total_count = await service.list_curricula(
            filters=filters,
            skip=skip,
            limit=limit,
            current_user_id=current_user.user_id
        )
        
        return {
            "items": curricula,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": total_count > skip + len(curricula)
        }
        
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{curriculum_id}", response_model=CurriculumDetail)
async def get_curriculum(
    curriculum_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Get curriculum details by ID
    
    Returns detailed information about a specific curriculum.
    Users can only access their own curricula unless they are admin/recruiter.
    """
    try:
        return await service.get_curriculum(curriculum_id, current_user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{curriculum_id}/download")
async def download_curriculum(
    curriculum_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Download curriculum file
    
    Returns the original file content with appropriate headers.
    Users can only download their own curricula unless they are admin/recruiter.
    """
    try:
        file_content, file_name, content_type = await service.download_curriculum(
            curriculum_id, current_user.user_id
        )
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{file_name}\"",
                "Content-Length": str(len(file_content))
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{curriculum_id}", response_model=CurriculumDetail)
async def update_curriculum(
    curriculum_id: UUID,
    curriculum_data: CurriculumUpdate,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Update curriculum
    
    Update curriculum information. Only the owner can update their curriculum.
    
    **Optional fields:**
    - **file_name**: New file name
    - **is_work**: Update work status
    - **file_base64**: Update file content
    - **file_path**: Update file path
    """
    try:
        return await service.update_curriculum(curriculum_id, curriculum_data, current_user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_curriculum(
    curriculum_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Delete curriculum (soft delete)
    
    Marks the curriculum as deleted. Only the owner can delete their curriculum.
    This is a soft delete - the data is preserved but marked as deleted.
    """
    try:
        success = await service.delete_curriculum(curriculum_id, current_user.user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao deletar currículo"
            )
        return None
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =============================================
# USER-SPECIFIC ENDPOINTS
# =============================================

@router.get("/user/{user_id}", response_model=List[CurriculumResponse])
async def get_user_curricula(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Get all curricula for a specific user
    
    Returns all curricula belonging to the specified user.
    Users can only access their own curricula unless they are admin/recruiter.
    """
    try:
        return await service.get_user_curricula(user_id, current_user.user_id, skip, limit)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/me/curricula", response_model=List[CurriculumResponse])
async def get_my_curricula(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Get current user's curricula
    
    Returns all curricula belonging to the currently authenticated user.
    """
    try:
        return await service.get_user_curricula(current_user.user_id, current_user.user_id, skip, limit)
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =============================================
# PROCESSING ENDPOINTS
# =============================================

@router.post("/{curriculum_id}/process", response_model=dict)
async def process_curriculum(
    curriculum_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Process curriculum with LLM
    
    Extracts and analyzes data from the curriculum using AI/LLM.
    This endpoint starts the processing and returns the results.
    
    **Processing includes:**
    - Text extraction from file
    - Personal information extraction
    - Experience and skills analysis
    - Education background parsing
    - Competency scoring
    """
    try:
        result = await service.process_curriculum(curriculum_id, current_user.user_id)
        return {
            "message": "Currículo processado com sucesso",
            "processing_result": result
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =============================================
# STATISTICS AND ANALYTICS ENDPOINTS
# =============================================

@router.get("/statistics/overview", response_model=CurriculumStatistics)
async def get_curriculum_statistics(
    user_id: Optional[UUID] = Query(None, description="Get statistics for specific user (admin only)"),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Get curriculum statistics
    
    Returns statistics about curricula usage and distribution.
    
    **For regular users:** Returns their own statistics
    **For admin users:** Returns system-wide statistics or specific user statistics if user_id provided
    """
    try:
        # Non-admin users can only see their own statistics
        if current_user.user_type != "admin":
            user_id = current_user.user_id
        elif user_id is None:
            # Admin requesting system-wide statistics
            user_id = None
        
        return await service.get_statistics(user_id)
        
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =============================================
# SEARCH ENDPOINTS
# =============================================

@router.get("/search/advanced", response_model=dict)
async def advanced_search(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_name: Optional[str] = Query(None, description="Search in file names"),
    file_type: Optional[FileTypeEnum] = Query(None, description="Filter by file type"),
    is_work: Optional[bool] = Query(None, description="Filter by work curriculum"),
    uploaded_after: Optional[str] = Query(None, description="Filter uploaded after date (YYYY-MM-DD)"),
    uploaded_before: Optional[str] = Query(None, description="Filter uploaded before date (YYYY-MM-DD)"),
    current_user: UserResponse = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Advanced curriculum search
    
    Provides advanced search capabilities with multiple filters.
    Non-admin users can only search their own curricula.
    
    **Date format:** YYYY-MM-DD (e.g., 2024-01-15)
    """
    try:
        from datetime import datetime
        
        # Parse dates
        uploaded_after_dt = None
        uploaded_before_dt = None
        
        if uploaded_after:
            try:
                uploaded_after_dt = datetime.strptime(uploaded_after, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data 'uploaded_after' deve estar no formato YYYY-MM-DD"
                )
        
        if uploaded_before:
            try:
                uploaded_before_dt = datetime.strptime(uploaded_before, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data 'uploaded_before' deve estar no formato YYYY-MM-DD"
                )
        
        # Build filters
        filters = CurriculumSearchFilters(
            file_name=file_name,
            file_type=file_type,
            is_work=is_work,
            uploaded_after=uploaded_after_dt,
            uploaded_before=uploaded_before_dt
        )
        
        curricula, total_count = await service.list_curricula(
            filters=filters,
            skip=skip,
            limit=limit,
            current_user_id=current_user.user_id
        )
        
        return {
            "items": curricula,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": total_count > skip + len(curricula),
            "filters_applied": {
                "file_name": file_name,
                "file_type": file_type,
                "is_work": is_work,
                "uploaded_after": uploaded_after,
                "uploaded_before": uploaded_before
            }
        }
        
    except AppException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =============================================
# HEALTH CHECK ENDPOINT
# =============================================

@router.get("/health")
async def curriculum_health_check():
    """
    Health check for curriculum service
    
    Returns the status of the curriculum service.
    """
    return {
        "service": "curriculum",
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "upload",
            "download", 
            "processing",
            "search",
            "statistics"
        ]
    }