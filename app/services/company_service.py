# =============================================
# app/services/company_service.py
# =============================================
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import JobRepository
from app.schemas.company import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyResponse, 
    CompanyDetail, 
    CompanySummary,
    CompanySearchFilters,
    CompanyStatistics
)
from app.core.exceptions import AppException, UserNotFoundError

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.user_repo = UserRepository(db)
        self.job_repo = JobRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_company(self, company_data: CompanyCreate, create_user_id: Optional[UUID] = None) -> CompanyResponse:
        """Create a new company with business validations"""
        try:
            # Validate CNPJ uniqueness
            existing_company = await self.company_repo.get_by_cnpj(company_data.cnpj)
            if existing_company:
                raise AppException("CNPJ já está em uso por outra empresa")
            
            # Validate address if provided
            if company_data.address_id:
                # In a full implementation, you would validate address exists
                pass
            
            # Create company
            company = await self.company_repo.create(company_data, create_user_id)
            
            logger.info(f"Company created successfully: {company.company_name} (ID: {company.company_id})")
            return CompanyResponse.model_validate(company)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise AppException(f"Erro ao criar empresa: {str(e)}")
    
    async def get_company(self, company_id: UUID) -> CompanyDetail:
        """Get company by ID with detailed information"""
        try:
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Get additional statistics
            stats = await self.company_repo.get_statistics(company_id)
            
            # Convert to detail response with stats
            company_detail = CompanyDetail.model_validate(company)
            company_detail.total_jobs = stats.get("total_jobs", 0)
            company_detail.active_jobs = stats.get("active_jobs", 0)
            company_detail.total_users = stats.get("total_users", 0)
            
            return company_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting company {company_id}: {e}")
            raise AppException(f"Erro ao buscar empresa: {str(e)}")
    
    async def get_companies(self, skip: int = 0, limit: int = 100) -> List[CompanyResponse]:
        """Get all companies with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            companies = await self.company_repo.get_all(skip=skip, limit=limit)
            return [CompanyResponse.model_validate(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            raise AppException(f"Erro ao listar empresas: {str(e)}")
    
    async def update_company(self, company_id: UUID, company_data: CompanyUpdate) -> CompanyDetail:
        """Update company with business validations"""
        try:
            # Check if company exists
            existing_company = await self.company_repo.get_by_id(company_id)
            if not existing_company:
                raise AppException("Empresa não encontrada")
            
            # Validate CNPJ uniqueness if being updated
            if company_data.cnpj:
                cnpj_exists = await self.company_repo.cnpj_exists(company_data.cnpj, exclude_company_id=company_id)
                if cnpj_exists:
                    raise AppException("CNPJ já está em uso por outra empresa")
            
            # Update company
            updated_company = await self.company_repo.update(company_id, company_data)
            if not updated_company:
                raise AppException("Erro ao atualizar empresa")
            
            logger.info(f"Company updated successfully: {company_id}")
            return await self.get_company(company_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {e}")
            raise AppException(f"Erro ao atualizar empresa: {str(e)}")
    
    async def delete_company(self, company_id: UUID) -> bool:
        """Delete company (soft delete) with business validations"""
        try:
            # Check if company exists
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Check if company has active jobs
            job_count = await self.job_repo.get_company_jobs_count(company_id)
            if job_count > 0:
                raise AppException("Não é possível excluir empresa com vagas ativas")
            
            # Check if company has users
            # In a full implementation, you would check for linked users
            
            success = await self.company_repo.soft_delete(company_id)
            if success:
                logger.info(f"Company deleted successfully: {company_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {e}")
            raise AppException(f"Erro ao deletar empresa: {str(e)}")
    
    # =============================================
    # BUSINESS SPECIFIC OPERATIONS
    # =============================================
    
    async def add_user_to_company(self, company_id: UUID, user_id: UUID) -> bool:
        """Add user to company"""
        try:
            # Validate company exists
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            # Check if user is already linked to another company
            if user.company_id and user.company_id != company_id:
                raise AppException("Usuário já está vinculado a outra empresa")
            
            # Update user with company_id
            from app.schemas.user import UserUpdate
            user_update = UserUpdate(company_id=company_id)
            updated_user = await self.user_repo.update(user_id, user_update)
            
            if updated_user:
                logger.info(f"User {user_id} added to company {company_id}")
                return True
            
            return False
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error adding user to company: {e}")
            raise AppException(f"Erro ao adicionar usuário à empresa: {str(e)}")
    
    async def remove_user_from_company(self, company_id: UUID, user_id: UUID) -> bool:
        """Remove user from company"""
        try:
            # Validate user exists and belongs to company
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("Usuário não encontrado")
            
            if user.company_id != company_id:
                raise AppException("Usuário não pertence a esta empresa")
            
            # Remove user from company
            from app.schemas.user import UserUpdate
            user_update = UserUpdate(company_id=None)
            updated_user = await self.user_repo.update(user_id, user_update)
            
            if updated_user:
                logger.info(f"User {user_id} removed from company {company_id}")
                return True
            
            return False
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error removing user from company: {e}")
            raise AppException(f"Erro ao remover usuário da empresa: {str(e)}")
    
    async def get_company_details(self, company_id: UUID) -> CompanyDetail:
        """Get comprehensive company details with related data"""
        try:
            company = await self.company_repo.get_with_details(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Get comprehensive statistics
            stats = await self.get_company_statistics(company_id)
            
            # Convert to detail response
            company_detail = CompanyDetail.model_validate(company)
            
            # Add statistics
            company_detail.total_jobs = stats.total_jobs
            company_detail.active_jobs = stats.active_jobs
            company_detail.total_users = stats.total_users
            
            return company_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting company details {company_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da empresa: {str(e)}")
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_companies(self, filters: CompanySearchFilters, skip: int = 0, limit: int = 100) -> List[CompanySummary]:
        """Search companies with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            companies = await self.company_repo.search(filters, skip=skip, limit=limit)
            return [CompanySummary.model_validate(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise AppException(f"Erro ao buscar empresas: {str(e)}")
    
    async def get_companies_count(self, filters: Optional[CompanySearchFilters] = None) -> int:
        """Get total count of companies matching filters"""
        try:
            return await self.company_repo.get_count(filters)
        except Exception as e:
            logger.error(f"Error getting companies count: {e}")
            raise AppException(f"Erro ao contar empresas: {str(e)}")
    
    async def get_companies_with_jobs(self, skip: int = 0, limit: int = 100) -> List[CompanySummary]:
        """Get companies that have active jobs"""
        try:
            if limit > 1000:
                limit = 1000
                
            companies = await self.company_repo.get_companies_with_jobs(skip=skip, limit=limit)
            return [CompanySummary.model_validate(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error getting companies with jobs: {e}")
            raise AppException(f"Erro ao buscar empresas com vagas: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_company_statistics(self, company_id: UUID) -> CompanyStatistics:
        """Get comprehensive company statistics"""
        try:
            # Validate company exists
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            # Get basic statistics
            stats = await self.company_repo.get_statistics(company_id)
            
            # Get job statistics
            jobs = await self.job_repo.get_by_company(company_id)
            total_jobs = len(jobs)
            active_jobs = sum(1 for job in jobs if job.deleted_date is None)
            closed_jobs = total_jobs - active_jobs
            
            # Calculate additional metrics
            total_applications = 0
            for job in jobs:
                job_app_count = await self.job_repo.get_job_application_count(job.job_id) if hasattr(self.job_repo, 'get_job_application_count') else 0
                total_applications += job_app_count
            
            avg_applications_per_job = total_applications / total_jobs if total_jobs > 0 else 0.0
            
            # Find most applied job
            most_applied_job = None
            max_applications = 0
            for job in jobs:
                job_app_count = await self.job_repo.get_job_application_count(job.job_id) if hasattr(self.job_repo, 'get_job_application_count') else 0
                if job_app_count > max_applications:
                    max_applications = job_app_count
                    most_applied_job = job.job_name
            
            return CompanyStatistics(
                company_id=company_id,
                total_jobs=total_jobs,
                active_jobs=active_jobs,
                closed_jobs=closed_jobs,
                total_applications=total_applications,
                total_users=stats.get("total_users", 0),
                avg_applications_per_job=avg_applications_per_job,
                most_applied_job=most_applied_job
            )
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting company statistics {company_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas da empresa: {str(e)}")
    
    async def get_top_companies_by_jobs(self, limit: int = 10) -> List[Dict]:
        """Get top companies by number of active jobs"""
        try:
            return await self.company_repo.get_top_companies_by_jobs(limit=limit)
        except Exception as e:
            logger.error(f"Error getting top companies by jobs: {e}")
            raise AppException(f"Erro ao obter ranking de empresas: {str(e)}")
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def validate_cnpj_availability(self, cnpj: str, exclude_company_id: Optional[UUID] = None) -> bool:
        """Check if CNPJ is available for use"""
        try:
            exists = await self.company_repo.cnpj_exists(cnpj, exclude_company_id)
            return not exists
        except Exception as e:
            logger.error(f"Error validating CNPJ availability: {e}")
            return False
    
    async def company_exists(self, company_id: UUID) -> bool:
        """Check if company exists"""
        try:
            return await self.company_repo.exists(company_id)
        except Exception as e:
            logger.error(f"Error checking if company exists: {e}")
            return False
    
    # =============================================
    # BULK OPERATIONS
    # =============================================
    
    async def bulk_add_users_to_company(self, company_id: UUID, user_ids: List[UUID]) -> Dict[str, List[UUID]]:
        """Add multiple users to company"""
        try:
            # Validate company exists
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise AppException("Empresa não encontrada")
            
            added_users = []
            failed_users = []
            
            for user_id in user_ids:
                try:
                    success = await self.add_user_to_company(company_id, user_id)
                    if success:
                        added_users.append(user_id)
                    else:
                        failed_users.append(user_id)
                except Exception as e:
                    logger.warning(f"Failed to add user {user_id} to company {company_id}: {e}")
                    failed_users.append(user_id)
            
            logger.info(f"Bulk add users to company {company_id}: {len(added_users)} added, {len(failed_users)} failed")
            
            return {
                "added_users": added_users,
                "failed_users": failed_users,
                "total_added": len(added_users),
                "total_failed": len(failed_users)
            }
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error in bulk add users to company: {e}")
            raise AppException(f"Erro ao adicionar usuários em lote: {str(e)}")
    
    # =============================================
    # BUSINESS RULES VALIDATION
    # =============================================
    
    async def can_delete_company(self, company_id: UUID) -> Dict[str, any]:
        """Check if company can be deleted and return reasons if not"""
        try:
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                return {"can_delete": False, "reasons": ["Empresa não encontrada"]}
            
            reasons = []
            
            # Check for active jobs
            job_count = await self.job_repo.get_company_jobs_count(company_id)
            if job_count > 0:
                reasons.append(f"Empresa possui {job_count} vaga(s) ativa(s)")
            
            # Check for linked users (this would need to be implemented in user_repo)
            # user_count = await self.user_repo.get_company_user_count(company_id)
            # if user_count > 0:
            #     reasons.append(f"Empresa possui {user_count} usuário(s) vinculado(s)")
            
            can_delete = len(reasons) == 0
            
            return {
                "can_delete": can_delete,
                "reasons": reasons,
                "company_name": company.company_name
            }
            
        except Exception as e:
            logger.error(f"Error checking if company can be deleted: {e}")
            return {"can_delete": False, "reasons": ["Erro interno"]}
    
    async def validate_company_data(self, company_data: CompanyCreate) -> Dict[str, List[str]]:
        """Validate company data and return validation errors"""
        try:
            errors = {}
            
            # Validate CNPJ
            if await self.company_repo.cnpj_exists(company_data.cnpj):
                errors.setdefault("cnpj", []).append("CNPJ já está em uso")
            
            # Add other business validations here
            # For example, validate company name length, format, etc.
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating company data: {e}")
            return {"general": ["Erro na validação dos dados"]}