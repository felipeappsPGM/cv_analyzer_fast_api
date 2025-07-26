# =============================================
# app/repositories/company_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, Dict
from uuid import UUID
import logging

from app.database.models.company import Company
from app.database.models.job import Job
from app.database.models.user import User
from app.database.models.address import Address
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanySearchFilters
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create(self, company_data: CompanyCreate, create_user_id: Optional[UUID] = None) -> Company:
        """Create a new company"""
        try:
            db_company = Company(
                company_name=company_data.company_name,
                area_of_activity=company_data.area_of_activity,
                cnpj=company_data.cnpj,
                address_id=company_data.address_id,
                create_user_id=create_user_id
            )
            
            self.db.add(db_company)
            await self.db.commit()
            await self.db.refresh(db_company)
            
            logger.info(f"Company created successfully: {db_company.company_id}")
            return db_company
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating company: {e}")
            if "cnpj" in str(e).lower():
                raise AppException("CNPJ já está em uso")
            raise AppException("Erro de integridade ao criar empresa")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating company: {e}")
            raise AppException(f"Erro ao criar empresa: {str(e)}")
    
    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        try:
            stmt = select(Company).where(
                and_(Company.company_id == company_id, Company.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting company by ID {company_id}: {e}")
            raise AppException(f"Erro ao buscar empresa: {str(e)}")
    
    async def get_by_cnpj(self, cnpj: str) -> Optional[Company]:
        """Get company by CNPJ"""
        try:
            stmt = select(Company).where(
                and_(Company.cnpj == cnpj, Company.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting company by CNPJ {cnpj}: {e}")
            raise AppException(f"Erro ao buscar empresa por CNPJ: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get all companies with pagination"""
        try:
            stmt = select(Company).where(
                Company.deleted_date.is_(None)
            ).offset(skip).limit(limit).order_by(Company.company_name)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all companies: {e}")
            raise AppException(f"Erro ao listar empresas: {str(e)}")
    
    async def update(self, company_id: UUID, company_data: CompanyUpdate) -> Optional[Company]:
        """Update company"""
        try:
            # Get only non-None fields
            update_data = company_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(company_id)
            
            stmt = update(Company).where(
                and_(Company.company_id == company_id, Company.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(company_id)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating company {company_id}: {e}")
            if "cnpj" in str(e).lower():
                raise AppException("CNPJ já está em uso")
            raise AppException("Erro de integridade ao atualizar empresa")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating company {company_id}: {e}")
            raise AppException(f"Erro ao atualizar empresa: {str(e)}")
    
    async def soft_delete(self, company_id: UUID) -> bool:
        """Soft delete company"""
        try:
            from datetime import datetime
            
            stmt = update(Company).where(
                and_(Company.company_id == company_id, Company.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Company soft deleted: {company_id}")
            return success
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error soft deleting company {company_id}: {e}")
            raise AppException(f"Erro ao deletar empresa: {str(e)}")
    
    # =============================================
    # SPECIFIC QUERIES
    # =============================================
    
    async def get_companies_with_jobs(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get companies that have active jobs"""
        try:
            stmt = (
                select(Company)
                .join(Job, Company.company_id == Job.company_id)
                .where(
                    and_(
                        Company.deleted_date.is_(None),
                        Job.deleted_date.is_(None)
                    )
                )
                .distinct()
                .offset(skip)
                .limit(limit)
                .order_by(Company.company_name)
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting companies with jobs: {e}")
            raise AppException(f"Erro ao buscar empresas com vagas: {str(e)}")
    
    async def get_with_details(self, company_id: UUID) -> Optional[Company]:
        """Get company with related data loaded"""
        try:
            stmt = (
                select(Company)
                .options(
                    selectinload(Company.jobs),
                    selectinload(Company.users),
                    selectinload(Company.addresses)
                )
                .where(
                    and_(Company.company_id == company_id, Company.deleted_date.is_(None))
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting company details {company_id}: {e}")
            raise AppException(f"Erro ao buscar detalhes da empresa: {str(e)}")
    
    async def search(self, filters: CompanySearchFilters, skip: int = 0, limit: int = 100) -> List[Company]:
        """Search companies with filters"""
        try:
            stmt = select(Company).where(Company.deleted_date.is_(None))
            
            # Apply filters
            if filters.company_name:
                stmt = stmt.where(
                    Company.company_name.ilike(f"%{filters.company_name}%")
                )
            
            if filters.area_of_activity:
                stmt = stmt.where(
                    Company.area_of_activity.ilike(f"%{filters.area_of_activity}%")
                )
            
            if filters.cnpj:
                stmt = stmt.where(Company.cnpj == filters.cnpj)
            
            if filters.has_active_jobs is not None:
                if filters.has_active_jobs:
                    stmt = stmt.join(Job, Company.company_id == Job.company_id).where(
                        Job.deleted_date.is_(None)
                    ).distinct()
                else:
                    # Companies without active jobs
                    subquery = select(Job.company_id).where(Job.deleted_date.is_(None))
                    stmt = stmt.where(Company.company_id.notin_(subquery))
            
            if filters.created_after:
                stmt = stmt.where(Company.created_date >= filters.created_after)
            
            if filters.created_before:
                stmt = stmt.where(Company.created_date <= filters.created_before)
            
            # Add pagination and ordering
            stmt = stmt.offset(skip).limit(limit).order_by(Company.company_name)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise AppException(f"Erro ao buscar empresas: {str(e)}")
    
    async def get_count(self, filters: Optional[CompanySearchFilters] = None) -> int:
        """Get total count of companies matching filters"""
        try:
            stmt = select(func.count(Company.company_id)).where(Company.deleted_date.is_(None))
            
            if filters:
                if filters.company_name:
                    stmt = stmt.where(
                        Company.company_name.ilike(f"%{filters.company_name}%")
                    )
                
                if filters.area_of_activity:
                    stmt = stmt.where(
                        Company.area_of_activity.ilike(f"%{filters.area_of_activity}%")
                    )
                
                if filters.cnpj:
                    stmt = stmt.where(Company.cnpj == filters.cnpj)
                
                if filters.has_active_jobs is not None:
                    if filters.has_active_jobs:
                        stmt = stmt.join(Job, Company.company_id == Job.company_id).where(
                            Job.deleted_date.is_(None)
                        )
                    else:
                        subquery = select(Job.company_id).where(Job.deleted_date.is_(None))
                        stmt = stmt.where(Company.company_id.notin_(subquery))
            
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting companies count: {e}")
            raise AppException(f"Erro ao contar empresas: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_statistics(self, company_id: UUID) -> Dict:
        """Get company statistics"""
        try:
            # Get basic counts
            total_jobs_stmt = select(func.count(Job.job_id)).where(
                and_(Job.company_id == company_id, Job.deleted_date.is_(None))
            )
            
            active_jobs_stmt = select(func.count(Job.job_id)).where(
                and_(Job.company_id == company_id, Job.deleted_date.is_(None))
            )
            
            total_users_stmt = select(func.count(User.user_id)).where(
                and_(User.company_id == company_id, User.deleted_date.is_(None))
            )
            
            # Execute queries
            total_jobs_result = await self.db.execute(total_jobs_stmt)
            active_jobs_result = await self.db.execute(active_jobs_stmt)
            total_users_result = await self.db.execute(total_users_stmt)
            
            total_jobs = total_jobs_result.scalar() or 0
            active_jobs = active_jobs_result.scalar() or 0
            total_users = total_users_result.scalar() or 0
            
            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "closed_jobs": total_jobs - active_jobs,
                "total_users": total_users,
                "total_applications": 0,  # Will be calculated with proper joins
                "avg_applications_per_job": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting company statistics {company_id}: {e}")
            raise AppException(f"Erro ao obter estatísticas da empresa: {str(e)}")
    
    async def get_top_companies_by_jobs(self, limit: int = 10) -> List[Dict]:
        """Get top companies by number of active jobs"""
        try:
            stmt = (
                select(
                    Company.company_id,
                    Company.company_name,
                    func.count(Job.job_id).label('job_count')
                )
                .join(Job, Company.company_id == Job.company_id)
                .where(
                    and_(
                        Company.deleted_date.is_(None),
                        Job.deleted_date.is_(None)
                    )
                )
                .group_by(Company.company_id, Company.company_name)
                .order_by(func.count(Job.job_id).desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "company_id": row.company_id,
                    "company_name": row.company_name,
                    "job_count": row.job_count
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting top companies by jobs: {e}")
            raise AppException(f"Erro ao obter ranking de empresas: {str(e)}")
    
    # =============================================
    # UTILITY METHODS
    # =============================================
    
    async def exists(self, company_id: UUID) -> bool:
        """Check if company exists"""
        try:
            stmt = select(Company.company_id).where(
                and_(Company.company_id == company_id, Company.deleted_date.is_(None))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if company exists {company_id}: {e}")
            return False
    
    async def cnpj_exists(self, cnpj: str, exclude_company_id: Optional[UUID] = None) -> bool:
        """Check if CNPJ is already in use"""
        try:
            stmt = select(Company.company_id).where(
                and_(Company.cnpj == cnpj, Company.deleted_date.is_(None))
            )
            
            if exclude_company_id:
                stmt = stmt.where(Company.company_id != exclude_company_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if CNPJ exists {cnpj}: {e}")
            return False