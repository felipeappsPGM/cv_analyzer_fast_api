# =============================================
# app/api/v1/endpoints/companies.py
# =============================================
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID

from app.config.database import get_db
from app.services.company_service import CompanyService
from app.schemas.company import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyResponse, 
    CompanyDetail, 
    CompanySummary,
    CompanySearchFilters,
    CompanyStatistics
)
from app.schemas.user import UserResponse
from app.api.v1.endpoints.auth import get_current_user, require_recruiter_or_admin

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_company_service(db: AsyncSession = Depends(get_db)) -> CompanyService:
    return CompanyService(db)

# =============================================
# COMPANY CRUD ROUTES
# =============================================

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Criar nova empresa
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **company_name**: Nome da empresa
    - **area_of_activity**: Área de atividade da empresa (opcional)
    - **cnpj**: CNPJ da empresa (único)
    - **address_id**: ID do endereço (opcional)
    """
    return await company_service.create_company(company_data, create_user_id=current_user.user_id)

@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Listar empresas com paginação
    
    **Requer autenticação**
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    return await company_service.get_companies(skip=skip, limit=limit)

@router.get("/search", response_model=List[CompanySummary])
async def search_companies(
    company_name: Optional[str] = Query(None, description="Filtrar por nome da empresa"),
    area_of_activity: Optional[str] = Query(None, description="Filtrar por área de atividade"),
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ"),
    has_active_jobs: Optional[bool] = Query(None, description="Filtrar empresas com vagas ativas"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Buscar empresas com filtros avançados
    
    **Requer autenticação**
    
    Permite filtrar empresas por diversos critérios.
    """
    filters = CompanySearchFilters(
        company_name=company_name,
        area_of_activity=area_of_activity,
        cnpj=cnpj,
        has_active_jobs=has_active_jobs
    )
    
    return await company_service.search_companies(filters, skip=skip, limit=limit)

@router.get("/with-jobs", response_model=List[CompanySummary])
async def get_companies_with_jobs(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Listar empresas que possuem vagas ativas
    
    **Requer autenticação**
    
    Retorna apenas empresas que possuem pelo menos uma vaga ativa.
    """
    return await company_service.get_companies_with_jobs(skip=skip, limit=limit)

@router.get("/count")
async def get_companies_count(
    company_name: Optional[str] = Query(None, description="Filtrar por nome da empresa"),
    area_of_activity: Optional[str] = Query(None, description="Filtrar por área de atividade"),
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ"),
    has_active_jobs: Optional[bool] = Query(None, description="Filtrar empresas com vagas ativas"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Contar total de empresas que atendem aos filtros
    
    **Requer autenticação**
    
    Retorna o número total de empresas sem retornar os dados.
    """
    filters = CompanySearchFilters(
        company_name=company_name,
        area_of_activity=area_of_activity,
        cnpj=cnpj,
        has_active_jobs=has_active_jobs
    ) if any([company_name, area_of_activity, cnpj, has_active_jobs]) else None
    
    count = await company_service.get_companies_count(filters)
    return {"total": count, "filters_applied": filters is not None}

@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(
    company_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Obter empresa por ID
    
    **Requer autenticação**
    
    Retorna informações detalhadas da empresa incluindo estatísticas.
    """
    return await company_service.get_company(company_id)

@router.put("/{company_id}", response_model=CompanyDetail)
async def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Atualizar empresa
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite atualização parcial dos dados da empresa.
    Apenas os campos fornecidos serão atualizados.
    """
    return await company_service.update_company(company_id, company_data)

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Deletar empresa (soft delete)
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Marca a empresa como deletada sem remover do banco de dados.
    Não é possível deletar empresas com vagas ativas.
    """
    await company_service.delete_company(company_id)

# =============================================
# COMPANY USER MANAGEMENT ROUTES
# =============================================

@router.post("/{company_id}/users/{user_id}")
async def add_user_to_company(
    company_id: UUID,
    user_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Adicionar usuário à empresa
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Vincula um usuário específico à empresa.
    """
    success = await company_service.add_user_to_company(company_id, user_id)
    
    return {
        "success": success,
        "message": "Usuário adicionado à empresa com sucesso" if success else "Falha ao adicionar usuário à empresa",
        "company_id": company_id,
        "user_id": user_id
    }

@router.delete("/{company_id}/users/{user_id}")
async def remove_user_from_company(
    company_id: UUID,
    user_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Remover usuário da empresa
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Remove a vinculação do usuário com a empresa.
    """
    success = await company_service.remove_user_from_company(company_id, user_id)
    
    return {
        "success": success,
        "message": "Usuário removido da empresa com sucesso" if success else "Falha ao remover usuário da empresa",
        "company_id": company_id,
        "user_id": user_id
    }

@router.post("/{company_id}/users/bulk")
async def bulk_add_users_to_company(
    company_id: UUID,
    user_ids: List[UUID],
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Adicionar múltiplos usuários à empresa
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Adiciona uma lista de usuários à empresa de uma só vez.
    Retorna quais foram adicionados com sucesso e quais falharam.
    """
    result = await company_service.bulk_add_users_to_company(company_id, user_ids)
    
    return {
        "company_id": company_id,
        "total_requested": len(user_ids),
        "successfully_added": result["total_added"],
        "failed_additions": result["total_failed"],
        "added_user_ids": result["added_users"],
        "failed_user_ids": result["failed_users"],
        "message": f"Processamento concluído: {result['total_added']} usuários adicionados, {result['total_failed']} falharam"
    }

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/{company_id}/statistics", response_model=CompanyStatistics)
async def get_company_statistics(
    company_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Obter estatísticas da empresa
    
    **Requer autenticação**
    
    Retorna estatísticas detalhadas incluindo:
    - Total de vagas (ativas e fechadas)
    - Total de candidaturas
    - Média de candidaturas por vaga
    - Vaga com mais candidaturas
    """
    return await company_service.get_company_statistics(company_id)

@router.get("/analytics/top-by-jobs")
async def get_top_companies_by_jobs(
    limit: int = Query(10, ge=1, le=50, description="Limite de empresas no ranking"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Ranking das empresas com mais vagas ativas
    
    **Requer autenticação**
    
    Retorna as empresas ordenadas por número de vagas ativas.
    """
    ranking = await company_service.get_top_companies_by_jobs(limit=limit)
    
    return {
        "ranking": ranking,
        "total_companies": len(ranking),
        "limit": limit
    }

# =============================================
# VALIDATION ROUTES
# =============================================

@router.get("/{company_id}/exists")
async def check_company_exists(
    company_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Verificar se empresa existe
    
    **Requer autenticação**
    
    Retorna se a empresa existe sem retornar seus dados.
    """
    exists = await company_service.company_exists(company_id)
    
    return {
        "exists": exists,
        "company_id": company_id
    }

@router.get("/validate/cnpj/{cnpj}")
async def validate_cnpj_availability(
    cnpj: str,
    exclude_company_id: Optional[UUID] = Query(None, description="ID da empresa a excluir da validação"),
    current_user: UserResponse = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Validar disponibilidade de CNPJ
    
    **Requer autenticação**
    
    Verifica se o CNPJ está disponível para uso.
    Útil para validação em tempo real durante criação/edição.
    """
    is_available = await company_service.validate_cnpj_availability(cnpj, exclude_company_id)
    
    return {
        "cnpj": cnpj,
        "is_available": is_available,
        "message": "CNPJ disponível" if is_available else "CNPJ já está em uso"
    }

@router.get("/{company_id}/can-delete")
async def check_can_delete_company(
    company_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    Verificar se empresa pode ser deletada
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Verifica se a empresa pode ser deletada e retorna os motivos caso não possa.
    """
    result = await company_service.can_delete_company(company_id)
    
    return {
        "company_id": company_id,
        "can_delete": result["can_delete"],
        "reasons": result.get("reasons", []),
        "company_name": result.get("company_name"),
        "message": "Empresa pode ser deletada" if result["can_delete"] else "Empresa não pode ser deletada"
    }