# =============================================
# app/services/professional_profile_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.professional_profile_repository import ProfessionalProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.professional_experience_repository import ProfessionalExperienceRepository
from app.repositories.academic_background_repository import AcademicBackgroundRepository
from app.repositories.professional_courses_repository import ProfessionalCoursesRepository
from app.schemas.professional_profile import (
    ProfessionalProfileCreate, 
    ProfessionalProfileUpdate, 
    ProfessionalProfileResponse, 
    ProfessionalProfileDetail, 
    ProfessionalProfileSummary,
    ProfessionalProfileSearchFilters,
    ProfessionalProfileStatistics,
    ProfileCompletenessInfo
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class ProfessionalProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfessionalProfileRepository(db)
        self.user_repo = UserRepository(db)
        # Note: These repositories would need to be implemented
        # self.experience_repo = ProfessionalExperienceRepository(db)
        # self.academic_repo = AcademicBackgroundRepository(db)
        # self.courses_repo = ProfessionalCoursesRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_profile(self, profile_data: ProfessionalProfileCreate, create_user_id: Optional[UUID] = None) -> ProfessionalProfileResponse:
        """Create a new professional profile with business validations (BR07: Allow incomplete profiles)"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(profile_data.user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # BR07: Allow creation with minimal information (name is sufficient)
            # Additional validations for referenced IDs if provided
            if profile_data.academic_background_id:
                # In a full implementation, validate academic background exists and belongs to user
                pass
            
            if profile_data.professional_experience_id:
                # In a full implementation, validate experience exists and belongs to user
                pass
            
            if profile_data.professional_courses_id:
                # In a full implementation, validate courses exist and belong to user
                pass
            
            # Create profile
            profile = await self.profile_repo.create(profile_data, create_user_id)
            
            logger.info(f"Professional profile created successfully: {profile.professional_profile_name} (ID: {profile.professional_profile_id})")
            return ProfessionalProfileResponse.model_validate(profile)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating professional profile: {e}")
            raise AppException(f"Erro ao criar perfil profissional: {str(e)}")
    
    async def get_profile(self, profile_id: UUID) -> ProfessionalProfileDetail:
        """Get professional profile by ID with detailed information"""
        try:
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                raise AppException("Perfil profissional não encontrado")
            
            # Get user information
            user = await self.user_repo.get_by_id(profile.user_id)
            
            # Get statistics
            stats = await self.profile_repo.get_statistics(profile_id)
            
            # Calculate completeness
            completeness = await self.calculate_profile_completeness(profile_id)
            
            # Convert to detail response with additional info
            profile_detail = ProfessionalProfileDetail.model_validate(profile)
            
            # Add user information
            if user:
                profile_detail.user_name = user.user_name
                profile_detail.user_email = user.user_email
            
            # Add statistics
            profile_detail.total_applications = stats.get("total_applications", 0)
            profile_detail.total_analyses = stats.get("total_analyses", 0)
            profile_detail.avg_score = stats.get("avg_score")
            
            # Add completeness information
            profile_detail.has_academic_background = profile.academic_background_id is not None
            profile_detail.has_professional_experience = profile.professional_experience_id is not None
            profile_detail.has_professional_courses = profile.professional_courses_id is not None
            profile_detail.completeness_percentage = completeness["completeness_percentage"]
            
            return profile_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting professional profile {profile_id}: {e}")
            raise AppException(f"Erro ao buscar perfil profissional: {str(e)}")
    
    async def get_profiles(self, skip: int = 0, limit: int = 100) -> List[ProfessionalProfileResponse]:
        """Get all professional profiles with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            profiles = await self.profile_repo.get_all(skip=skip, limit=limit)
            return [ProfessionalProfileResponse.model_validate(profile) for profile in profiles]
            
        except Exception as e:
            logger.error(f"Error getting professional profiles: {e}")
            raise AppException(f"Erro ao listar perfis profissionais: {str(e)}")
    
    async def update_profile(self, profile_id: UUID, profile_data: ProfessionalProfileUpdate) -> ProfessionalProfileDetail:
        """Update professional profile with business validations"""
        try:
            # Check if profile exists
            existing_profile = await self.profile_repo.get_by_id(profile_id)
            if not existing_profile:
                raise AppException("Perfil profissional não encontrado")
            
            # Validate referenced IDs if being updated
            if profile_data.academic_background_id:
                # In a full implementation, validate academic background exists and belongs to user
                pass
            
            if profile_data.professional_experience_id:
                # In a full implementation, validate experience exists and belongs to user
                pass
            
            if profile_data.professional_courses_id:
                # In a full implementation, validate courses exist and belong to user
                pass
            
            # Update profile
            updated_profile = await self.profile_repo.update(profile_id, profile_data)
            if not updated_profile:
                raise AppException("Erro ao atualizar perfil profissional")
            
            logger.info(f"Professional profile updated successfully: {profile_id}")
            return await self.get_profile(profile_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating professional profile {profile_id}: {e}")
            raise AppException(f"Erro ao atualizar perfil profissional: {str(e)}")
    
    async def delete_profile(self, profile_id: UUID) -> bool:
        """Delete professional profile (soft delete) with business validations"""
        try:
            # Check if profile exists
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                raise AppException("Perfil profissional não encontrado")
            
            # Check if profile has applications (may want to prevent deletion)
            stats = await self.profile_repo.get_statistics(profile_id)
            if stats.get("total_applications", 0) > 0:
                raise AppException("Não é possível excluir perfil com candidaturas ativas")
            
            success = await self.profile_repo.soft_delete(profile_id)
            if success:
                logger.info(f"Professional profile deleted successfully: {profile_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting professional profile {profile_id}: {e}")
            raise AppException(f"Erro ao deletar perfil profissional: {str(e)}")
    
    # =============================================
    # USER SPECIFIC OPERATIONS
    # =============================================
    
    async def get_user_profiles(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ProfessionalProfileSummary]:
        """Get all professional profiles for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            profiles = await self.profile_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary with completeness info
            profile_summaries = []
            for profile in profiles:
                summary = ProfessionalProfileSummary.model_validate(profile)
                summary.user_name = user.user_name
                
                # Calculate completeness
                completeness = await self.calculate_profile_completeness(profile.professional_profile_id)
                summary.completeness_percentage = completeness["completeness_percentage"]
                
                profile_summaries.append(summary)
            
            return profile_summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user profiles {user_id}: {e}")
            raise AppException(f"Erro ao buscar perfis profissionais do usuário: {str(e)}")
    
    async def get_user_primary_profile(self, user_id: UUID) -> Optional[ProfessionalProfileDetail]:
        """Get user's primary (most recent) professional profile"""
        try:
            profile = await self.profile_repo.get_user_primary_profile(user_id)
            if not profile:
                return None
            
            return await self.get_profile(profile.professional_profile_id)
            
        except Exception as e:
            logger.error(f"Error getting user primary profile {user_id}: {e}")
            return None
    
    async def create_user_first_profile(self, user_id: UUID, profile_name: str, description: Optional[str] = None) -> ProfessionalProfileResponse:
        """Create user's first professional profile with minimal data (BR07)"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Check if user already has profiles
            existing_profiles = await self.profile_repo.get_by_user(user_id, limit=1)
            if existing_profiles:
                raise AppException("Usuário já possui perfil profissional")
            
            # Create minimal profile (BR07: Allow incomplete)
            profile_data = ProfessionalProfileCreate(
                professional_profile_name=profile_name,
                professional_profile_description=description,
                user_id=user_id
            )
            
            return await self.create_profile(profile_data, create_user_id=user_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating user first profile: {e}")
            raise AppException(f"Erro ao criar primeiro perfil: {str(e)}")
    
    # =============================================
    # PROFILE COMPLETENESS AND ENHANCEMENT
    # =============================================
    
    async def calculate_profile_completeness(self, profile_id: UUID) -> Dict:
        """Calculate profile completeness percentage and missing items"""
        try:
            # Use repository method for basic calculation
            completeness = await self.profile_repo.calculate_completeness(profile_id)
            
            # Enhanced completeness calculation
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                return {"completeness_percentage": 0, "missing_items": [], "completed_items": []}
            
            # Define weighted criteria for completeness
            criteria = {
                "basic_info": {
                    "weight": 25,
                    "complete": bool(profile.professional_profile_name and profile.professional_profile_description),
                    "description": "Informações básicas (nome e descrição)"
                },
                "academic_background": {
                    "weight": 25,
                    "complete": profile.academic_background_id is not None,
                    "description": "Formação acadêmica"
                },
                "professional_experience": {
                    "weight": 35,
                    "complete": profile.professional_experience_id is not None,
                    "description": "Experiência profissional"
                },
                "professional_courses": {
                    "weight": 15,
                    "complete": profile.professional_courses_id is not None,
                    "description": "Cursos profissionais"
                }
            }
            
            # Calculate weighted completeness
            total_weight = sum(criterion["weight"] for criterion in criteria.values())
            completed_weight = sum(
                criterion["weight"] for criterion in criteria.values() 
                if criterion["complete"]
            )
            
            completeness_percentage = (completed_weight / total_weight) * 100
            
            # Generate suggestions
            missing_items = [
                criterion["description"] for criterion in criteria.values() 
                if not criterion["complete"]
            ]
            
            completed_items = [
                criterion["description"] for criterion in criteria.values() 
                if criterion["complete"]
            ]
            
            suggestions = []
            if not criteria["basic_info"]["complete"]:
                suggestions.append("Complete o nome e descrição do perfil")
            if not criteria["professional_experience"]["complete"]:
                suggestions.append("Adicione sua experiência profissional")
            if not criteria["academic_background"]["complete"]:
                suggestions.append("Cadastre sua formação acadêmica")
            if not criteria["professional_courses"]["complete"]:
                suggestions.append("Inclua cursos e certificações relevantes")
            
            return {
                "completeness_percentage": round(completeness_percentage, 1),
                "missing_items": missing_items,
                "completed_items": completed_items,
                "suggestions": suggestions,
                "criteria_details": criteria
            }
            
        except Exception as e:
            logger.error(f"Error calculating profile completeness {profile_id}: {e}")
            return {"completeness_percentage": 0, "missing_items": [], "completed_items": []}
    
    async def get_profile_completeness_info(self, profile_id: UUID) -> ProfileCompletenessInfo:
        """Get detailed profile completeness information"""
        try:
            completeness_data = await self.calculate_profile_completeness(profile_id)
            
            return ProfileCompletenessInfo(
                professional_profile_id=profile_id,
                completeness_percentage=completeness_data["completeness_percentage"],
                missing_items=completeness_data["missing_items"],
                completed_items=completeness_data["completed_items"],
                suggestions=completeness_data["suggestions"],
                basic_info_complete=completeness_data["criteria_details"]["basic_info"]["complete"],
                academic_complete=completeness_data["criteria_details"]["academic_background"]["complete"],
                experience_complete=completeness_data["criteria_details"]["professional_experience"]["complete"],
                courses_complete=completeness_data["criteria_details"]["professional_courses"]["complete"]
            )
            
        except Exception as e:
            logger.error(f"Error getting profile completeness info: {e}")
            raise AppException(f"Erro ao obter informações de completude: {str(e)}")
    
    async def get_improvement_suggestions(self, profile_id: UUID) -> List[str]:
        """Get personalized suggestions to improve profile"""
        try:
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                return []
            
            completeness = await self.calculate_profile_completeness(profile_id)
            suggestions = completeness.get("suggestions", [])
            
            # Add personalized suggestions based on profile analysis
            stats = await self.profile_repo.get_statistics(profile_id)
            
            if stats.get("avg_score") and stats["avg_score"] < 70:
                suggestions.append("Considere adicionar mais detalhes sobre suas competências")
            
            if stats.get("total_applications", 0) > 0 and stats.get("total_analyses", 0) == 0:
                suggestions.append("Aguarde as análises das suas candidaturas para insights específicos")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting improvement suggestions: {e}")
            return []
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_profiles(self, filters: ProfessionalProfileSearchFilters, skip: int = 0, limit: int = 100) -> List[ProfessionalProfileSummary]:
        """Search professional profiles with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            profiles = await self.profile_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            profile_summaries = []
            for profile in profiles:
                summary = ProfessionalProfileSummary.model_validate(profile)
                
                # Get user info
                user = await self.user_repo.get_by_id(profile.user_id)
                if user:
                    summary.user_name = user.user_name
                
                # Calculate completeness
                completeness = await self.calculate_profile_completeness(profile.professional_profile_id)
                summary.completeness_percentage = completeness["completeness_percentage"]
                
                profile_summaries.append(summary)
            
            return profile_summaries
            
        except Exception as e:
            logger.error(f"Error searching professional profiles: {e}")
            raise AppException(f"Erro ao buscar perfis profissionais: {str(e)}")
    
    async def get_profiles_count(self, filters: Optional[ProfessionalProfileSearchFilters] = None) -> int:
        """Get total count of professional profiles matching filters"""
        try:
            return await self.profile_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting profiles count: {e}")
            raise AppException(f"Erro ao contar perfis profissionais: {str(e)}")
    
    async def get_profiles_by_completeness(self, min_completeness: float, skip: int = 0, limit: int = 100) -> List[ProfessionalProfileSummary]:
        """Get profiles with completeness above threshold"""
        try:
            if limit > 1000:
                limit = 1000
            
            profiles = await self.profile_repo.get_profiles_by_completeness(min_completeness, skip=skip, limit=limit)
            
            # Convert to summary with completeness info
            profile_summaries = []
            for profile in profiles:
                summary = ProfessionalProfileSummary.model_validate(profile)
                
                # Get user info
                user = await self.user_repo.get_by_id(profile.user_id)
                if user:
                    summary.user_name = user.user_name
                
                # Calculate exact completeness
                completeness = await self.calculate_profile_completeness(profile.professional_profile_id)
                summary.completeness_percentage = completeness["completeness_percentage"]
                
                # Only include if meets threshold
                if summary.completeness_percentage >= min_completeness:
                    profile_summaries.append(summary)
            
            return profile_summaries
            
        except Exception as e:
            logger.error(f"Error getting profiles by completeness: {e}")
            raise AppException(f"Erro ao buscar perfis por completude: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_profile_statistics(self, profile_id: UUID) -> ProfessionalProfileStatistics:
        """Get comprehensive profile statistics"""
        try:
            # Validate profile exists
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                raise AppException("Perfil profissional não encontrado")
            
            # Get statistics from repository
            stats = await self.profile_repo.get_statistics(profile_id)
            
            # Get performance data
            # This would require integration with analysis repository
            
            return ProfessionalProfileStatistics(
                professional_profile_id=profile_id,
                total_applications=stats.get("total_applications", 0),
                # successful_applications=...,  # Would need status tracking
                # pending_applications=...,
                avg_score=stats.get("avg_score"),
                highest_score=stats.get("highest_score")
                # best_performing_skills=...,  # Would need skill extraction
                # improvement_areas=...,
                # application_trend=...  # Would need time series data
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting profile statistics {profile_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas do perfil: {str(e)}")
    
    async def get_top_performing_profiles(self, min_score: float = 80, limit: int = 50) -> List[Dict]:
        """Get top performing profiles by analysis scores"""
        try:
            return await self.profile_repo.get_profiles_by_performance(min_score, limit)
        except Exception as e:
            logger.error(f"Error getting top performing profiles: {e}")
            raise AppException(f"Erro ao obter perfis de alto desempenho: {str(e)}")
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def profile_exists(self, profile_id: UUID) -> bool:
        """Check if professional profile exists"""
        try:
            return await self.profile_repo.exists(profile_id)
        except Exception as e:
            logger.error(f"Error checking if profile exists: {e}")
            return False
    
    async def user_has_profile(self, user_id: UUID) -> bool:
        """Check if user has at least one professional profile"""
        try:
            profiles = await self.profile_repo.get_by_user(user_id, limit=1)
            return len(profiles) > 0
        except Exception as e:
            logger.error(f"Error checking if user has profile: {e}")
            return False
    
    async def validate_profile_ownership(self, profile_id: UUID, user_id: UUID) -> bool:
        """Validate that profile belongs to user"""
        try:
            profile = await self.profile_repo.get_by_id(profile_id)
            return profile is not None and profile.user_id == user_id
        except Exception as e:
            logger.error(f"Error validating profile ownership: {e}")
            return False
    
    # =============================================
    # BUSINESS RULES VALIDATION
    # =============================================
    
    async def can_delete_profile(self, profile_id: UUID) -> Dict[str, any]:
        """Check if profile can be deleted and return reasons if not"""
        try:
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                return {"can_delete": False, "reasons": ["Perfil não encontrado"]}
            
            reasons = []
            
            # Check for applications
            stats = await self.profile_repo.get_statistics(profile_id)
            if stats.get("total_applications", 0) > 0:
                reasons.append(f"Perfil possui {stats['total_applications']} candidatura(s)")
            
            # Check for analyses
            if stats.get("total_analyses", 0) > 0:
                reasons.append(f"Perfil possui {stats['total_analyses']} análise(s)")
            
            can_delete = len(reasons) == 0
            
            return {
                "can_delete": can_delete,
                "reasons": reasons,
                "profile_name": profile.professional_profile_name
            }
            
        except Exception as e:
            logger.error(f"Error checking if profile can be deleted: {e}")
            return {"can_delete": False, "reasons": ["Erro interno"]}
    
    async def validate_profile_data(self, profile_data: ProfessionalProfileCreate) -> Dict[str, List[str]]:
        """Validate profile data and return validation errors"""
        try:
            errors = {}
            
            # Validate user exists
            if not await self.user_repo.exists(profile_data.user_id):
                errors.setdefault("user_id", []).append("Usuário não encontrado")
            
            # Validate referenced IDs if provided
            if profile_data.academic_background_id:
                # In a full implementation, validate academic background exists
                pass
            
            if profile_data.professional_experience_id:
                # In a full implementation, validate experience exists
                pass
            
            if profile_data.professional_courses_id:
                # In a full implementation, validate courses exist
                pass
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating profile data: {e}")
            return {"general": ["Erro na validação dos dados"]}