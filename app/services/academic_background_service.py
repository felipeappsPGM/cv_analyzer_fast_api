# =============================================
# app/services/academic_background_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.academic_background_repository import AcademicBackgroundRepository
from app.repositories.user_repository import UserRepository
from app.schemas.academic_background import (
    AcademicBackgroundCreate,
    AcademicBackgroundUpdate,
    AcademicBackgroundResponse,
    AcademicBackgroundDetail,
    AcademicBackgroundSummary,
    AcademicBackgroundSearchFilters,
    AcademicBackgroundStatistics,
    DegreeTypeEnum
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class AcademicBackgroundService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.academic_repo = AcademicBackgroundRepository(db)
        self.user_repo = UserRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_academic_background(self, academic_data: AcademicBackgroundCreate, create_user_id: Optional[UUID] = None) -> AcademicBackgroundResponse:
        """Create a new academic background with business validations"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(academic_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Create academic background
            academic = await self.academic_repo.create(academic_data, create_user_id)
            
            logger.info(f"Academic background created successfully: {academic.degree_name} at {academic.institution_name} (ID: {academic.academic_background_id})")
            return AcademicBackgroundResponse.model_validate(academic)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating academic background: {e}")
            raise AppException(f"Erro ao criar formação acadêmica: {str(e)}")
    
    async def get_academic_background(self, academic_id: UUID) -> AcademicBackgroundDetail:
        """Get academic background by ID with detailed information"""
        try:
            academic = await self.academic_repo.get_by_id(academic_id)
            if not academic:
                raise AppException("Formação acadêmica não encontrada")
            
            # Get user information
            user = await self.user_repo.get_by_id(academic.user_id)
            
            # Convert to detail response with additional info
            academic_detail = AcademicBackgroundDetail.model_validate(academic)
            
            # Add user information
            if user:
                academic_detail.user_name = user.user_name
            
            return academic_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting academic background {academic_id}: {e}")
            raise AppException(f"Erro ao buscar formação acadêmica: {str(e)}")
    
    async def get_academic_backgrounds(self, skip: int = 0, limit: int = 100) -> List[AcademicBackgroundResponse]:
        """Get all academic backgrounds with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            academics = await self.academic_repo.get_all(skip=skip, limit=limit)
            return [AcademicBackgroundResponse.model_validate(academic) for academic in academics]
            
        except Exception as e:
            logger.error(f"Error getting academic backgrounds: {e}")
            raise AppException(f"Erro ao listar formações acadêmicas: {str(e)}")
    
    async def update_academic_background(self, academic_id: UUID, academic_data: AcademicBackgroundUpdate) -> AcademicBackgroundDetail:
        """Update academic background with business validations"""
        try:
            # Check if academic background exists
            existing_academic = await self.academic_repo.get_by_id(academic_id)
            if not existing_academic:
                raise AppException("Formação acadêmica não encontrada")
            
            # Update academic background
            updated_academic = await self.academic_repo.update(academic_id, academic_data)
            if not updated_academic:
                raise AppException("Erro ao atualizar formação acadêmica")
            
            logger.info(f"Academic background updated successfully: {academic_id}")
            return await self.get_academic_background(academic_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating academic background {academic_id}: {e}")
            raise AppException(f"Erro ao atualizar formação acadêmica: {str(e)}")
    
    async def delete_academic_background(self, academic_id: UUID) -> bool:
        """Delete academic background (soft delete)"""
        try:
            # Check if academic background exists
            academic = await self.academic_repo.get_by_id(academic_id)
            if not academic:
                raise AppException("Formação acadêmica não encontrada")
            
            success = await self.academic_repo.soft_delete(academic_id)
            if success:
                logger.info(f"Academic background deleted successfully: {academic_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting academic background {academic_id}: {e}")
            raise AppException(f"Erro ao deletar formação acadêmica: {str(e)}")
    
    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================
    
    async def get_user_academic_backgrounds(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AcademicBackgroundSummary]:
        """Get all academic backgrounds for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            academics = await self.academic_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary
            academic_summaries = []
            for academic in academics:
                summary = AcademicBackgroundSummary.model_validate(academic)
                academic_summaries.append(summary)
            
            return academic_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user academic backgrounds {user_id}: {e}")
            raise AppException(f"Erro ao buscar formações acadêmicas do usuário: {str(e)}")
    
    async def get_user_highest_degree(self, user_id: UUID) -> Optional[AcademicBackgroundDetail]:
        """Get user's highest degree"""
        try:
            academic = await self.academic_repo.get_highest_degree(user_id)
            if not academic:
                return None
            
            return await self.get_academic_background(academic.academic_background_id)
            
        except Exception as e:
            logger.error(f"Error getting highest degree for user {user_id}: {e}")
            return None
    
    async def get_user_degree_progression(self, user_id: UUID) -> List[Dict]:
        """Get user's academic progression timeline"""
        try:
            return await self.academic_repo.get_degree_progression(user_id)
            
        except Exception as e:
            logger.error(f"Error getting degree progression for user {user_id}: {e}")
            raise AppException(f"Erro ao obter progressão acadêmica: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_academic_backgrounds(self, filters: AcademicBackgroundSearchFilters, skip: int = 0, limit: int = 100) -> List[AcademicBackgroundSummary]:
        """Search academic backgrounds with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            academics = await self.academic_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary
            academic_summaries = []
            for academic in academics:
                summary = AcademicBackgroundSummary.model_validate(academic)
                academic_summaries.append(summary)
            
            return academic_summaries
            
        except Exception as e:
            logger.error(f"Error searching academic backgrounds: {e}")
            raise AppException(f"Erro ao buscar formações acadêmicas: {str(e)}")
    
    async def get_academic_backgrounds_count(self, filters: Optional[AcademicBackgroundSearchFilters] = None) -> int:
        """Get total count of academic backgrounds matching filters"""
        try:
            return await self.academic_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting academic backgrounds count: {e}")
            raise AppException(f"Erro ao contar formações acadêmicas: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_user_statistics(self, user_id: UUID) -> AcademicBackgroundStatistics:
        """Get comprehensive statistics for user's academic backgrounds"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Get statistics from repository
            stats = await self.academic_repo.get_statistics(user_id)
            
            # Get academic progression for trends
            academic_progression = await self.academic_repo.get_degree_progression(user_id)
            
            return AcademicBackgroundStatistics(
                user_id=user_id,
                total_academic_backgrounds=stats["total_academic_backgrounds"],
                completed_degrees=stats["completed_degrees"],
                ongoing_degrees=stats["ongoing_degrees"],
                highest_degree_type=DegreeTypeEnum(stats["highest_degree_type"]) if stats["highest_degree_type"] else None,
                total_study_duration_months=stats["total_study_duration_months"],
                total_study_duration_years=stats["total_study_duration_years"],
                institutions_attended=stats["institutions_attended"],
                fields_of_study=stats["fields_of_study"],
                degree_types_completed=[DegreeTypeEnum(dt) for dt in stats["degree_types_completed"]],
                academic_progression={"timeline": academic_progression}
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user academic statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas acadêmicas: {str(e)}")
    
    async def get_institutions_ranking(self, limit: int = 10) -> List[Dict]:
        """Get most common institutions"""
        try:
            return await self.academic_repo.get_institutions_ranking(limit)
        except Exception as e:
            logger.error(f"Error getting institutions ranking: {e}")
            raise AppException(f"Erro ao obter ranking de instituições: {str(e)}")
    
    async def get_fields_of_study_distribution(self) -> List[Dict]:
        """Get distribution of fields of study"""
        try:
            return await self.academic_repo.get_fields_of_study_distribution()
        except Exception as e:
            logger.error(f"Error getting fields distribution: {e}")
            raise AppException(f"Erro ao obter distribuição de áreas: {str(e)}")
    
    # =============================================
    # BUSINESS LOGIC HELPERS
    # =============================================
    
    async def calculate_education_score(self, user_id: UUID) -> float:
        """Calculate education score based on degrees (0-100)"""
        try:
            # Get user's academic backgrounds
            academics = await self.academic_repo.get_by_user(user_id, limit=100)
            
            if not academics:
                return 0.0
            
            # Define scoring weights for different degree types
            degree_scores = {
                DegreeTypeEnum.POS_DOUTORADO: 100,
                DegreeTypeEnum.DOUTORADO: 95,
                DegreeTypeEnum.MESTRADO: 85,
                DegreeTypeEnum.MBA: 80,
                DegreeTypeEnum.ESPECIALIZACAO: 75,
                DegreeTypeEnum.POS_GRADUACAO: 70,
                DegreeTypeEnum.GRADUACAO: 60,
                DegreeTypeEnum.TECNOLOGIA: 50,
                DegreeTypeEnum.TECNICO: 40,
                DegreeTypeEnum.ENSINO_MEDIO: 30
            }
            
            # Calculate score based on highest degree and number of degrees
            highest_score = 0
            bonus_points = 0
            
            for academic in academics:
                degree_type = DegreeTypeEnum(academic.degree_type)
                score = degree_scores.get(degree_type, 0)
                
                if score > highest_score:
                    highest_score = score
                
                # Bonus for multiple degrees (max 15 points)
                if score >= 60:  # Graduate level or higher
                    bonus_points += 3
            
            # Cap bonus at 15 points
            bonus_points = min(bonus_points, 15)
            
            # Final score (max 100)
            final_score = min(highest_score + bonus_points, 100)
            
            return float(final_score)
            
        except Exception as e:
            logger.error(f"Error calculating education score: {e}")
            return 0.0
    
    async def get_degree_recommendations(self, user_id: UUID) -> List[str]:
        """Get degree recommendations based on user's current education"""
        try:
            # Get user's highest degree
            highest_degree = await self.get_user_highest_degree(user_id)
            
            if not highest_degree:
                return ["Graduação", "Curso Técnico", "Ensino Médio"]
            
            # Recommend next level degrees
            recommendations = []
            current_type = highest_degree.degree_type
            
            if current_type == DegreeTypeEnum.ENSINO_MEDIO:
                recommendations = ["Graduação", "Curso Técnico", "Tecnólogo"]
            elif current_type == DegreeTypeEnum.TECNICO:
                recommendations = ["Graduação", "Tecnólogo"]
            elif current_type == DegreeTypeEnum.TECNOLOGIA:
                recommendations = ["Graduação", "Pós-graduação"]
            elif current_type == DegreeTypeEnum.GRADUACAO:
                recommendations = ["Pós-graduação", "Especialização", "MBA"]
            elif current_type in [DegreeTypeEnum.POS_GRADUACAO, DegreeTypeEnum.ESPECIALIZACAO]:
                recommendations = ["MBA", "Mestrado"]
            elif current_type == DegreeTypeEnum.MBA:
                recommendations = ["Mestrado", "Segunda Graduação"]
            elif current_type == DegreeTypeEnum.MESTRADO:
                recommendations = ["Doutorado", "Segunda Especialização"]
            elif current_type == DegreeTypeEnum.DOUTORADO:
                recommendations = ["Pós-doutorado", "Segunda Área de Especialização"]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting degree recommendations: {e}")
            return []
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def academic_background_exists(self, academic_id: UUID) -> bool:
        """Check if academic background exists"""
        try:
            return await self.academic_repo.exists(academic_id)
        except Exception as e:
            logger.error(f"Error checking if academic background exists: {e}")
            return False
    
    async def user_has_academic_backgrounds(self, user_id: UUID) -> bool:
        """Check if user has academic backgrounds"""
        try:
            count = await self.academic_repo.get_user_academic_count(user_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if user has academic backgrounds: {e}")
            return False
    
    async def user_has_degree_type(self, user_id: UUID, degree_type: DegreeTypeEnum) -> bool:
        """Check if user has a specific degree type"""
        try:
            return await self.academic_repo.has_degree_type(user_id, degree_type.value)
        except Exception as e:
            logger.error(f"Error checking degree type: {e}")
            return False
    
    async def validate_academic_data(self, academic_data: AcademicBackgroundCreate) -> Dict[str, List[str]]:
        """Validate academic data and return validation errors"""
        try:
            errors = {}
            
            # Validate user exists
            if not await self.user_repo.exists(academic_data.user_id):
                errors.setdefault("user_id", []).append("Usuário não encontrado")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating academic data: {e}")
            return {"general": ["Erro na validação dos dados"]}