# =============================================
# app/services/analysis_service.py
# =============================================
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
import asyncio

from app.repositories.analyze_application_job_repository import AnalyzeApplicationJobRepository
from app.repositories.application_job_repository import ApplicationJobRepository
from app.repositories.professional_profile_repository import ProfessionalProfileRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.analyze_application_job import (
    AnalyzeApplicationJobCreate, 
    AnalyzeApplicationJobUpdate, 
    AnalyzeApplicationJobResponse, 
    AnalyzeApplicationJobDetail, 
    AnalyzeApplicationJobSummary,
    AnalyzeApplicationJobSearchFilters,
    AnalysisRanking,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    AnalysisStatistics
)
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_repo = AnalyzeApplicationJobRepository(db)
        self.application_repo = ApplicationJobRepository(db)
        self.profile_repo = ProfessionalProfileRepository(db)
        self.job_repo = JobRepository(db)
        self.user_repo = UserRepository(db)
        self.curriculum_repo = CurriculumRepository(db)
    
    # =============================================
    # BASIC CRUD OPERATIONS
    # =============================================
    
    async def create_analysis(self, analysis_data: AnalyzeApplicationJobCreate, create_user_id: Optional[UUID] = None) -> AnalyzeApplicationJobResponse:
        """Create a new analysis with business rule validations (BR01-BR06: Weighted scoring)"""
        try:
            # Validate professional profile exists
            profile = await self.profile_repo.get_by_id(analysis_data.professional_profile_id)
            if not profile:
                raise AppException("Perfil profissional não encontrado")
            
            # Validate user exists
            user = await self.user_repo.get_by_id(analysis_data.user_id)
            if not user:
                raise AppException("Usuário não encontrado")
            
            # Validate that profile belongs to user
            if profile.user_id != analysis_data.user_id:
                raise AppException("Perfil profissional não pertence ao usuário")
            
            # Apply business rules BR01-BR06 for score calculation
            if analysis_data.total_score == 0.0:
                analysis_data.total_score = self._calculate_weighted_score(
                    academic_score=analysis_data.academic_score or 0,
                    experience_score=analysis_data.professional_experience_score or 0,
                    courses_score=analysis_data.professional_courses_score or 0,
                    strong_points_score=analysis_data.strong_points_score or 0,
                    weak_points_score=analysis_data.weak_points_score or 0
                )
            
            # Create analysis
            analysis = await self.analysis_repo.create(analysis_data, create_user_id)
            
            logger.info(f"Analysis created successfully: {analysis.analyze_application_job_id} with score {analysis.total_score}")
            return AnalyzeApplicationJobResponse.model_validate(analysis)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise AppException(f"Erro ao criar análise: {str(e)}")
    
    async def get_analysis(self, analysis_id: UUID) -> AnalyzeApplicationJobDetail:
        """Get analysis by ID with detailed information"""
        try:
            analysis = await self.analysis_repo.get_by_id(analysis_id)
            if not analysis:
                raise AppException("Análise não encontrada")
            
            # Get user and profile information
            user = await self.user_repo.get_by_id(analysis.user_id)
            profile = await self.profile_repo.get_by_id(analysis.professional_profile_id)
            
            # Convert to detail response with additional info
            analysis_detail = AnalyzeApplicationJobDetail.model_validate(analysis)
            
            # Add user information
            if user:
                analysis_detail.user_name = user.user_name
                analysis_detail.user_email = user.user_email
            
            # Add profile information
            if profile:
                analysis_detail.profile_name = profile.professional_profile_name
            
            # Calculate weighted breakdown (already handled by model validator)
            # Calculate score category (already handled by model validator)
            
            # Get ranking information if available
            try:
                # This would require finding which job this analysis relates to
                # For now, we'll leave these as None
                analysis_detail.percentile_rank = None
                analysis_detail.ranking_position = None
                analysis_detail.total_candidates = None
            except:
                pass
            
            return analysis_detail
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao buscar análise: {str(e)}")
    
    async def get_analyses(self, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJobResponse]:
        """Get all analyses with pagination"""
        try:
            if limit > 1000:
                limit = 1000
                
            analyses = await self.analysis_repo.get_all(skip=skip, limit=limit)
            return [AnalyzeApplicationJobResponse.model_validate(analysis) for analysis in analyses]
            
        except Exception as e:
            logger.error(f"Error getting analyses: {e}")
            raise AppException(f"Erro ao listar análises: {str(e)}")
    
    async def update_analysis(self, analysis_id: UUID, analysis_data: AnalyzeApplicationJobUpdate) -> AnalyzeApplicationJobDetail:
        """Update analysis with automatic score recalculation"""
        try:
            # Check if analysis exists
            existing_analysis = await self.analysis_repo.get_by_id(analysis_id)
            if not existing_analysis:
                raise AppException("Análise não encontrada")
            
            # If individual scores are being updated, the repository will recalculate total_score
            # Update analysis
            updated_analysis = await self.analysis_repo.update(analysis_id, analysis_data)
            if not updated_analysis:
                raise AppException("Erro ao atualizar análise")
            
            logger.info(f"Analysis updated successfully: {analysis_id}")
            return await self.get_analysis(analysis_id)
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao atualizar análise: {str(e)}")
    
    async def delete_analysis(self, analysis_id: UUID) -> bool:
        """Delete analysis (soft delete)"""
        try:
            # Check if analysis exists
            analysis = await self.analysis_repo.get_by_id(analysis_id)
            if not analysis:
                raise AppException("Análise não encontrada")
            
            success = await self.analysis_repo.soft_delete(analysis_id)
            if success:
                logger.info(f"Analysis deleted successfully: {analysis_id}")
            
            return success
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            raise AppException(f"Erro ao deletar análise: {str(e)}")
    
    # =============================================
    # JOB ANALYSIS AND RANKING
    # =============================================
    
    async def analyze_application(self, application_id: UUID, force_reanalysis: bool = False) -> AnalyzeApplicationJobResponse:
        """Analyze a job application using LLM (placeholder implementation)"""
        try:
            # Get application details
            application = await self.application_repo.get_with_details(application_id)
            if not application:
                raise AppException("Candidatura não encontrada")
            
            # Check if analysis already exists
            existing_analysis = await self.analysis_repo.get_by_profile(application.professional_profile_id)
            if existing_analysis and not force_reanalysis:
                raise AppException("Análise já existe para este perfil")
            
            # Get job details for analysis context
            job = await self.job_repo.get_with_details(application.job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get user's curriculum for analysis
            curriculum = await self.curriculum_repo.get_user_active_curriculum(application.user_id)
            
            # Placeholder for LLM analysis
            # In a real implementation, this would call the LLM service
            analysis_scores = await self._perform_llm_analysis(
                application=application,
                job=job,
                curriculum=curriculum
            )
            
            # Create analysis record
            analysis_data = AnalyzeApplicationJobCreate(
                professional_profile_id=application.professional_profile_id,
                user_id=application.user_id,
                academic_score=analysis_scores["academic_score"],
                professional_experience_score=analysis_scores["professional_experience_score"],
                professional_courses_score=analysis_scores["professional_courses_score"],
                weak_points_score=analysis_scores["weak_points_score"],
                strong_points_score=analysis_scores["strong_points_score"],
                total_score=0.0,  # Will be calculated automatically
                opinion_application_job=analysis_scores["opinion"]
            )
            
            analysis = await self.create_analysis(analysis_data)
            
            logger.info(f"Application analyzed successfully: {application_id}")
            return analysis
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing application {application_id}: {e}")
            raise AppException(f"Erro ao analisar candidatura: {str(e)}")
    
    async def get_job_ranking(self, job_id: UUID, limit: int = 50) -> List[AnalysisRanking]:
        """Get ranked analysis results for a job"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get ranked analyses for the job
            analyses = await self.analysis_repo.get_by_job_ranked(job_id, limit=limit)
            
            # Convert to ranking response
            rankings = []
            for idx, analysis in enumerate(analyses):
                # Get user information
                user = await self.user_repo.get_by_id(analysis.user_id)
                
                # Get application information
                # This would require a method to get application by profile and job
                # For now, we'll create a placeholder
                
                ranking = AnalysisRanking(
                    analyze_application_job_id=analysis.analyze_application_job_id,
                    application_job_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                    user_id=analysis.user_id,
                    user_name=user.user_name if user else "Usuário não encontrado",
                    user_email=user.user_email if user else "",
                    total_score=analysis.total_score,
                    ranking_position=idx + 1,
                    percentile_rank=(1 - (idx / len(analyses))) * 100,
                    academic_score=analysis.academic_score,
                    professional_experience_score=analysis.professional_experience_score,
                    professional_courses_score=analysis.professional_courses_score,
                    strong_points_score=analysis.strong_points_score,
                    weak_points_score=analysis.weak_points_score,
                    created_date=analysis.created_date
                )
                rankings.append(ranking)
            
            return rankings
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting job ranking {job_id}: {e}")
            raise AppException(f"Erro ao obter ranking da vaga: {str(e)}")
    
    async def generate_analysis_report(self, job_id: UUID) -> bytes:
        """Generate PDF analysis report for a job (placeholder implementation)"""
        try:
            # Validate job exists
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise AppException("Vaga não encontrada")
            
            # Get job statistics and ranking
            stats = await self.get_job_analysis_stats(job_id)
            ranking = await self.get_job_ranking(job_id, limit=100)
            
            # Placeholder for PDF generation
            # In a real implementation, this would use a PDF library like reportlab
            report_content = self._generate_pdf_report(job, stats, ranking)
            
            logger.info(f"Analysis report generated for job {job_id}")
            return report_content
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error generating analysis report {job_id}: {e}")
            raise AppException(f"Erro ao gerar relatório de análise: {str(e)}")
    
    # =============================================
    # USER ANALYSIS OPERATIONS
    # =============================================
    
    async def get_user_analyses(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJobSummary]:
        """Get all analyses for a specific user"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise AppException("Usuário não encontrado")
            
            if limit > 1000:
                limit = 1000
            
            analyses = await self.analysis_repo.get_by_user(user_id, skip=skip, limit=limit)
            
            # Convert to summary
            summaries = []
            for idx, analysis in enumerate(analyses):
                summary = AnalyzeApplicationJobSummary.model_validate(analysis)
                summary.user_name = user.user_name
                summary.ranking_position = None  # Would need job context to calculate
                summaries.append(summary)
            
            return summaries
            
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting user analyses {user_id}: {e}")
            raise AppException(f"Erro ao buscar análises do usuário: {str(e)}")
    
    async def get_user_best_analysis(self, user_id: UUID) -> Optional[AnalyzeApplicationJobDetail]:
        """Get user's best analysis result"""
        try:
            best_score = await self.analysis_repo.get_user_best_score(user_id)
            if not best_score:
                return None
            
            # Get analyses for user and find the one with best score
            analyses = await self.analysis_repo.get_by_user(user_id, limit=100)
            best_analysis = None
            
            for analysis in analyses:
                if analysis.total_score == best_score:
                    best_analysis = analysis
                    break
            
            if best_analysis:
                return await self.get_analysis(best_analysis.analyze_application_job_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user best analysis {user_id}: {e}")
            return None
    
    async def get_user_analysis_progress(self, user_id: UUID) -> Dict:
        """Get user's analysis progress and improvement trends"""
        try:
            analyses = await self.analysis_repo.get_by_user(user_id, limit=50)
            
            if not analyses:
                return {
                    "total_analyses": 0,
                    "avg_score": None,
                    "best_score": None,
                    "improvement_trend": "no_data",
                    "recent_analyses": []
                }
            
            # Calculate metrics
            scores = [a.total_score for a in analyses]
            total_analyses = len(analyses)
            avg_score = sum(scores) / total_analyses
            best_score = max(scores)
            
            # Calculate improvement trend (simple approach)
            if total_analyses >= 3:
                recent_scores = scores[:3]  # Last 3 analyses
                older_scores = scores[3:6] if len(scores) > 3 else scores[1:]
                
                if older_scores:
                    recent_avg = sum(recent_scores) / len(recent_scores)
                    older_avg = sum(older_scores) / len(older_scores)
                    
                    if recent_avg > older_avg + 5:
                        trend = "improving"
                    elif recent_avg < older_avg - 5:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
            else:
                trend = "insufficient_data"
            
            return {
                "total_analyses": total_analyses,
                "avg_score": round(avg_score, 1),
                "best_score": best_score,
                "improvement_trend": trend,
                "recent_analyses": [
                    {
                        "score": a.total_score,
                        "date": a.created_date,
                        "analysis_id": a.analyze_application_job_id
                    }
                    for a in analyses[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user analysis progress {user_id}: {e}")
            return {"total_analyses": 0, "avg_score": None, "best_score": None}
    
    # =============================================
    # BULK ANALYSIS OPERATIONS
    # =============================================
    
    async def bulk_analyze_applications(self, request: BulkAnalysisRequest) -> BulkAnalysisResponse:
        """Analyze multiple applications in bulk"""
        try:
            started_analyses = 0
            already_analyzed = 0
            failed_to_start = 0
            
            # Process each application
            for app_id in request.application_job_ids:
                try:
                    # Check if already analyzed
                    application = await self.application_repo.get_by_id(app_id)
                    if not application:
                        failed_to_start += 1
                        continue
                    
                    existing_analysis = await self.analysis_repo.get_by_profile(application.professional_profile_id)
                    if existing_analysis and not request.force_reanalysis:
                        already_analyzed += 1
                        continue
                    
                    # Start analysis (in a real implementation, this would be queued)
                    await self.analyze_application(app_id, force_reanalysis=request.force_reanalysis)
                    started_analyses += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to start analysis for application {app_id}: {e}")
                    failed_to_start += 1
            
            # Generate batch job ID (in real implementation, this would track the bulk operation)
            import uuid
            batch_job_id = uuid.uuid4()
            
            # Estimate completion time (placeholder)
            estimated_completion_minutes = max(1, started_analyses * 2)  # 2 minutes per analysis
            
            logger.info(f"Bulk analysis started: {started_analyses} analyses, batch {batch_job_id}")
            
            return BulkAnalysisResponse(
                total_requested=len(request.application_job_ids),
                started_analyses=started_analyses,
                already_analyzed=already_analyzed,
                failed_to_start=failed_to_start,
                analysis_job_id=batch_job_id,
                estimated_completion_minutes=estimated_completion_minutes
            )
            
        except Exception as e:
            logger.error(f"Error in bulk analyze applications: {e}")
            raise AppException(f"Erro na análise em lote: {str(e)}")
    
    # =============================================
    # STATISTICS AND ANALYTICS
    # =============================================
    
    async def get_analysis_statistics(self) -> AnalysisStatistics:
        """Get comprehensive analysis statistics"""
        try:
            # Get score distribution
            score_distribution = await self.analysis_repo.get_score_distribution()
            
            # Convert to enum-based distribution
            from app.schemas.analyze_application_job import ScoreCategoryEnum
            category_distribution = {}
            for item in score_distribution:
                if 90 <= item["min_score"] <= 100:
                    category_distribution[ScoreCategoryEnum.EXCELLENT] = item["count"]
                elif 80 <= item["min_score"] < 90:
                    category_distribution[ScoreCategoryEnum.VERY_GOOD] = item["count"]
                elif 70 <= item["min_score"] < 80:
                    category_distribution[ScoreCategoryEnum.GOOD] = item["count"]
                elif 60 <= item["min_score"] < 70:
                    category_distribution[ScoreCategoryEnum.SATISFACTORY] = item["count"]
                else:
                    category_distribution[ScoreCategoryEnum.NEEDS_IMPROVEMENT] = item["count"]
            
            # Get global ranking for top performers
            top_performers = await self.analysis_repo.get_global_ranking(limit=10)
            
            return AnalysisStatistics(
                total_analyses=sum(item["count"] for item in score_distribution),
                score_distribution=category_distribution,
                score_histogram=[
                    {"range": item["range"], "count": float(item["count"])}
                    for item in score_distribution
                ],
                top_performing_profiles=top_performers
            )
            
        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            raise AppException(f"Erro ao obter estatísticas de análises: {str(e)}")
    
    async def get_job_analysis_stats(self, job_id: UUID) -> Dict:
        """Get analysis statistics for a specific job"""
        try:
            return await self.analysis_repo.get_analysis_stats(job_id)
        except Exception as e:
            logger.error(f"Error getting job analysis stats: {e}")
            raise AppException(f"Erro ao obter estatísticas da vaga: {str(e)}")
    
    # =============================================
    # HELPER METHODS (PRIVATE)
    # =============================================
    
    def _calculate_weighted_score(self, academic_score: float, experience_score: float, 
                                courses_score: float, strong_points_score: float, 
                                weak_points_score: float) -> float:
        """Calculate weighted total score based on business rules BR01-BR06"""
        # BR01: Academic (30%), BR02: Experience (35%), BR03: Courses (20%)
        # BR04: Strong points (15%), BR05: Weak points (-10%)
        
        weighted_score = (
            (academic_score * 0.30) +           # BR01: 30%
            (experience_score * 0.35) +         # BR02: 35%
            (courses_score * 0.20) +            # BR03: 20%
            (strong_points_score * 0.15) -      # BR04: +15%
            (weak_points_score * 0.10)          # BR05: -10%
        )
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, weighted_score))
    
    async def _perform_llm_analysis(self, application, job, curriculum) -> Dict:
        """Placeholder for LLM analysis (would integrate with LLM service)"""
        # This is a placeholder implementation
        # In a real system, this would call the LLM service
        
        # Simulate analysis scores (in real implementation, these would come from LLM)
        import random
        
        academic_score = random.uniform(60, 95)
        experience_score = random.uniform(65, 90)
        courses_score = random.uniform(70, 85)
        strong_points_score = random.uniform(75, 95)
        weak_points_score = random.uniform(10, 30)
        
        opinion = f"Candidato apresenta perfil adequado para a vaga. Pontos fortes incluem experiência relevante. Áreas de melhoria identificadas em formação complementar."
        
        return {
            "academic_score": academic_score,
            "professional_experience_score": experience_score,
            "professional_courses_score": courses_score,
            "strong_points_score": strong_points_score,
            "weak_points_score": weak_points_score,
            "opinion": opinion
        }
    
    def _generate_pdf_report(self, job, stats, ranking) -> bytes:
        """Placeholder for PDF report generation"""
        # This is a placeholder implementation
        # In a real system, this would use a PDF library like reportlab
        
        report_text = f"""
        RELATÓRIO DE ANÁLISE DE CANDIDATOS
        
        Vaga: {job.job_name}
        Data: {datetime.now().strftime('%d/%m/%Y')}
        
        ESTATÍSTICAS:
        - Total de análises: {stats.get('total_analyses', 0)}
        - Pontuação média: {stats.get('avg_total_score', 0):.1f}
        - Maior pontuação: {stats.get('max_total_score', 0):.1f}
        
        TOP 10 CANDIDATOS:
        """
        
        for i, candidate in enumerate(ranking[:10]):
            report_text += f"{i+1}. {candidate.user_name} - {candidate.total_score:.1f} pontos\n"
        
        # Convert to bytes (in real implementation, this would be a proper PDF)
        return report_text.encode('utf-8')
    
    # =============================================
    # SEARCH AND FILTERING
    # =============================================
    
    async def search_analyses(self, filters: AnalyzeApplicationJobSearchFilters, skip: int = 0, limit: int = 100) -> List[AnalyzeApplicationJobSummary]:
        """Search analyses with advanced filters"""
        try:
            if limit > 1000:
                limit = 1000
            
            analyses = await self.analysis_repo.search(filters, skip=skip, limit=limit)
            
            # Convert to summary with additional info
            summaries = []
            for analysis in analyses:
                summary = AnalyzeApplicationJobSummary.model_validate(analysis)
                
                # Get user info
                user = await self.user_repo.get_by_id(analysis.user_id)
                if user:
                    summary.user_name = user.user_name
                
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error searching analyses: {e}")
            raise AppException(f"Erro ao buscar análises: {str(e)}")
    
    # =============================================
    # VALIDATION HELPERS
    # =============================================
    
    async def analysis_exists(self, analysis_id: UUID) -> bool:
        """Check if analysis exists"""
        try:
            return await self.analysis_repo.exists(analysis_id)
        except Exception as e:
            logger.error(f"Error checking if analysis exists: {e}")
            return False
    
    async def can_analyze_application(self, application_id: UUID) -> Dict[str, any]:
        """Check if application can be analyzed"""
        try:
            application = await self.application_repo.get_by_id(application_id)
            if not application:
                return {"can_analyze": False, "reasons": ["Candidatura não encontrada"]}
            
            reasons = []
            
            # Check if already analyzed
            existing_analysis = await self.analysis_repo.get_by_profile(application.professional_profile_id)
            if existing_analysis:
                reasons.append("Perfil já possui análise")
            
            # Check if job is still active
            job = await self.job_repo.get_by_id(application.job_id)
            if not job or job.deleted_date:
                reasons.append("Vaga não está mais ativa")
            
            can_analyze = len(reasons) == 0
            
            return {
                "can_analyze": can_analyze,
                "reasons": reasons,
                "has_existing_analysis": existing_analysis is not None
            }
            
        except Exception as e:
            logger.error(f"Error checking if can analyze application: {e}")
            return {"can_analyze": False, "reasons": ["Erro interno"]}