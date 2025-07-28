# =============================================
# app/services/professional_experience_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.professional_experience_repository import ProfessionalExperienceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.professional_experience import (
    ProfessionalExperienceCreate,
    ProfessionalExperienceUpdate,
    ProfessionalExperienceResponse,
    ProfessionalExperienceDetail,
    ProfessionalExperienceSummary,
    ProfessionalExperienceSearchFilters,
    ProfessionalExperienceStatistics
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class ProfessionalExperienceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.experience_repo = ProfessionalExperienceRepository(db)
        self.user_repo = UserRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_experience(self, experience_data: ProfessionalExperienceCreate, create_user_id: Optional[UUID] = None) -> ProfessionalExperienceResponse:
        """Create a new professional experience with business validations"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(experience_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Business rule: If marking as current, ensure no other current experience exists
            if experience_data.is_current:
                current_experience = await self.experience_repo.get_current_experience(experience_data.user_id)
                if current_experience:
                    raise AppException("Usuário já possui uma experiência profissional atual. Finalize a atual antes de adicionar uma nova.")
            
            # Create experience
            experience = await self.experience_repo.create(experience_data, create_user_id)
            
            logger.info(f"Professional experience created successfully: {experience.job_title} at {experience.company_name} (ID: {experience.professional_experience_id})")
            return ProfessionalExperienceResponse.model_validate(experience)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating professional experience: {e}")
            raise AppException(f"Erro ao criar experiência profissional: {str(e)}")
    
    async def get_experience(self, experience_id: UUID) -> ProfessionalExperienceDetail:
        """Get professional experience by ID with detailed information"""
        try:
            experience = await self.experience_repo.get_by_id(experience_id)
            if not experience:
                raise AppException("Experiência profissional não encontrada")
            
            # Get user information
            user = await self.user_repo.get_by_id(experience.user_id)
            
            # Convert to detail response with additional info
            experience_detail = ProfessionalExperienceDetail.model_validate(experience)
            
            # Add user information
            if user:
                experience_detail.user_name = user.user_name
            
            return experience_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting professional experience {experience_id}: {e}")
            raise AppException(f"Erro ao buscar experiência profissional: {str(e)}")
    
    async def get_experiences(self, skip: int = 0, limit: int = 100) -> List[ProfessionalExperienceResponse]:
        """Get all professional experiences with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            experiences = await self.experience_repo.get_all(skip=skip, limit=limit)
            return [ProfessionalExperienceResponse.model_validate(experience) for experience in experiences]
            
        except Exception as e:
            logger.error(f"Error getting professional experiences: {e}")
            raise AppException(f"Erro ao listar experiências profissionais: {str(e)}")
    
    async def update_experience(self, experience_id: UUID, experience_data: ProfessionalExperienceUpdate) -> ProfessionalExperienceDetail:
        """Update professional experience with business validations"""
        try:
            # Check if experience exists
            existing_experience = await self.experience_repo.get_by_id(experience_id)
            if not existing_experience:
                raise AppException("Experiência profissional não encontrada")
            
            # Business rule: If marking as current, ensure no other current experience exists
            if experience_data.is_current:
                current_experience = await self.experience_repo.get_current_experience(existing_experience.user_id)
                if current_experience and current_experience.professional_experience_id != experience_id:
                    raise AppException("Usuário já possui uma experiência profissional atual. Finalize a atual antes de marcar esta como atual.")
            
            # Update experience
            updated_experience = await self.experience_repo.update(experience_id, experience_data)
            if not updated_experience:
                raise AppException("Erro ao atualizar experiência profissional")
            
            logger.info(f"Professional experience updated successfully: {experience_id}")
            return await self.get_experience(experience_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating professional experience {experience_id}: {e}")
            raise AppException(f"Erro ao atualizar experiência profissional: {str(e)}")
    
    async def delete_experience(self, experience_id: UUID) -> bool:
        """Delete professional experience (soft delete)"""
        try:
            # Check if experience exists
            experience = await self.experience_repo.get_by_id(experience_id)
            if not experience:
                raise AppException("Experiência profissional não encontrada")
            
            success = await self.experience_repo.soft_delete(experience_id)
            if success:
                logger.info(f"Professional experience deleted successfully: {experience_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting professional experience {experience_id}: {e}")
            raise AppException(f"Erro ao deletar experiência profissional: {str(e)}")
    
    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================
    
    async def get_user_experiences(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalExperienceSummary]:
        """Get all professional experiences for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            experiences = await self.experience_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary
            experience_summaries = []
            for experience in experiences:
                summary = ProfessionalExperienceSummary.model_validate(experience)
                experience_summaries.append(summary)
            
            return experience_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user experiences {user_id}: {e}")
            raise AppException(f"Erro ao buscar experiências profissionais do usuário: {str(e)}")
    
    async def get_user_current_experience(self, user_id: UUID) -> Optional[ProfessionalExperienceDetail]:
        """Get user's current professional experience"""
        try:
            experience = await self.experience_repo.get_current_experience(user_id)
            if not experience:
                return None
            
            return await self.get_experience(experience.professional_experience_id)
            
        except Exception as e:
            logger.error(f"Error getting current experience for user {user_id}: {e}")
            return None
    
    async def get_user_experience_timeline(self, user_id: UUID) -> List[Dict]:
        """Get user's career progression timeline"""
        try:
            return await self.experience_repo.get_experience_trends(user_id)
            
        except Exception as e:
            logger.error(f"Error getting experience timeline for user {user_id}: {e}")
            raise AppException(f"Erro ao obter linha do tempo de experiências: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_experiences(self, filters: ProfessionalExperienceSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalExperienceSummary]:
        """Search professional experiences with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            experiences = await self.experience_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary
            experience_summaries = []
            for experience in experiences:
                summary = ProfessionalExperienceSummary.model_validate(experience)
                experience_summaries.append(summary)
            
            return experience_summaries
            
        except Exception as e:
            logger.error(f"Error searching professional experiences: {e}")
            raise AppException(f"Erro ao buscar experiências profissionais: {str(e)}")
    
    async def get_experiences_count(self, filters: Optional[ProfessionalExperienceSearchFilters] = None) -> int:
        """Get total count of professional experiences matching filters"""
        try:
            return await self.experience_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting experiences count: {e}")
            raise AppException(f"Erro ao contar experiências profissionais: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_user_statistics(self, user_id: UUID) -> ProfessionalExperienceStatistics:
        """Get comprehensive statistics for user's professional experiences"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Get statistics from repository
            stats = await self.experience_repo.get_statistics(user_id)
            
            # Get career progression for trends
            career_progression = await self.experience_repo.get_experience_trends(user_id)
            
            return ProfessionalExperienceStatistics(
                user_id=user_id,
                total_experiences=stats["total_experiences"],
                current_positions=stats["current_positions"],
                total_duration_months=stats["total_duration_months"],
                total_duration_years=stats["total_duration_years"],
                avg_duration_months=stats["avg_duration_months"],
                most_common_employment_type=stats["most_common_employment_type"],
                companies_worked=stats["companies_worked"],
                job_titles_held=stats["job_titles_held"],
                career_progression={"timeline": career_progression}
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user experience statistics {user_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas de experiência: {str(e)}")
    
    async def get_total_experience_years(self, user_id: UUID) -> float:
        """Calculate total years of experience for a user"""
        try:
            return await self.experience_repo.get_total_experience_years(user_id)
        except Exception as e:
            logger.error(f"Error calculating total experience years: {e}")
            return 0.0
    
    async def get_companies_worked(self, user_id: UUID) -> List[str]:
        """Get list of companies user has worked at"""
        try:
            return await self.experience_repo.get_companies_worked(user_id)
        except Exception as e:
            logger.error(f"Error getting companies worked: {e}")
            return []
    
    # =============================================
    # BUSINESS LOGIC HELPERS
    # =============================================
    
    async def calculate_seniority_level(self, user_id: UUID) -> str:
        """Calculate user's seniority level based on experience"""
        try:
            total_years = await self.get_total_experience_years(user_id)
            
            if total_years < 1:
                return "Júnior"
            elif total_years < 3:
                return "Pleno"
            elif total_years < 7:
                return "Sênior"
            else:
                return "Especialista"
                
        except Exception as e:
            logger.error(f"Error calculating seniority level: {e}")
            return "Não informado"
    
    async def get_job_recommendations(self, user_id: UUID) -> List[str]:
        """Get job recommendations based on user's experience"""
        try:
            # Get user's experience data
            experiences = await self.experience_repo.get_by_user(user_id, limit=10)
            
            if not experiences:
                return []
            
            # Extract job titles and companies for recommendation logic
            job_titles = [exp.job_title for exp in experiences]
            companies = [exp.company_name for exp in experiences]
            
            # Simple recommendation logic (in real app, this would be more sophisticated)
            recommendations = []
            if any("desenvolvedor" in title.lower() for title in job_titles):
                recommendations.extend(["Desenvolvedor Senior", "Tech Lead", "Arquiteto de Software"])
            if any("analista" in title.lower() for title in job_titles):
                recommendations.extend(["Coordenador", "Gerente", "Especialista"])
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error getting job recommendations: {e}")
            return []
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def experience_exists(self, experience_id: UUID) -> bool:
        """Check if professional experience exists"""
        try:
            return await self.experience_repo.exists(experience_id)
        except Exception as e:
            logger.error(f"Error checking if experience exists: {e}")
            return False
    
    async def user_has_experiences(self, user_id: UUID) -> bool:
        """Check if user has professional experiences"""
        try:
            count = await self.experience_repo.get_user_experience_count(user_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if user has experiences: {e}")
            return False
    
    async def validate_experience_data(self, experience_data: ProfessionalExperienceCreate) -> Dict[str, List[str]]:
        """Validate experience data and return validation errors"""
        try:
            errors = {}
            
            # Validate user exists
            if not await self.user_repo.exists(experience_data.user_id):
                errors.setdefault("user_id", []).append("Usuário não encontrado")
            
            # Validate current experience logic
            if experience_data.is_current:
                current_exp = await self.experience_repo.get_current_experience(experience_data.user_id)
                if current_exp:
                    errors.setdefault("is_current", []).append("Usuário já possui experiência atual")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating experience data: {e}")
            return {"general": ["Erro na validação dos dados"]}