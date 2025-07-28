# =============================================
# app/config/database.py
# =============================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, text
from typing import AsyncGenerator
import logging
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()

# Async Engine
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

# Session Factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base Model with metadata
metadata = MetaData()

class Base(DeclarativeBase):
    metadata = metadata

# =============================================
# DATABASE FUNCTIONS
# =============================================

# Dependency para obter sessão do banco
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obter sessão do banco de dados"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """
    Criar todas as tabelas no banco de dados
    
    Nota: Esta função não é mais necessária quando usando Alembic,
    mas mantida para compatibilidade com código existente.
    """
    try:
        # Com Alembic, as tabelas são criadas via migrações
        # Esta função agora apenas verifica se as tabelas existem
        logger.info("Verificando se as tabelas estão criadas via Alembic...")
        
        async with engine.begin() as conn:
            # Verificar se alguma tabela existe
            result = await conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
            table_count = result.scalar()
            logger.info(f"Encontradas {table_count} tabelas no banco de dados")
            
        if table_count == 0:
            logger.warning("Nenhuma tabela encontrada! Execute as migrações Alembic:")
            logger.warning("  python -m alembic upgrade head")
        else:
            logger.info("✅ Tabelas encontradas no banco de dados")
            
    except Exception as e:
        logger.error(f"Erro ao verificar tabelas: {e}")
        raise

async def drop_all_tables():
    """
    Remover todas as tabelas (usar com cuidado!)
    """
    try:
        logger.warning("🚨 REMOVENDO TODAS AS TABELAS!")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Todas as tabelas removidas")
    except Exception as e:
        logger.error(f"Erro ao remover tabelas: {e}")
        raise

# Health check function
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def get_database_info() -> dict:
    """Get database information"""
    try:
        async with async_session() as session:
            # Get database version
            version_result = await session.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # Get table count
            tables_result = await session.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
            table_count = tables_result.scalar()
            
            return {
                "status": "connected",
                "version": version,
                "table_count": table_count,
                "engine": str(engine.url)
            }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# =============================================
# CONNECTION MANAGEMENT
# =============================================

async def init_database():
    """Initialize database connection and verify setup"""
    try:
        logger.info("Inicializando conexão com banco de dados...")
        
        # Test connection
        is_healthy = await check_database_health()
        if not is_healthy:
            raise Exception("Não foi possível conectar ao banco de dados")
        
        # Get database info
        db_info = await get_database_info()
        logger.info(f"Conectado ao PostgreSQL: {db_info.get('table_count', 0)} tabelas")
        
        # Check if tables exist (created by Alembic)
        await create_tables()
        
        logger.info("✅ Banco de dados inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        raise

async def close_database():
    """Close database connections"""
    try:
        await engine.dispose()
        logger.info("Conexões com banco de dados fechadas")
    except Exception as e:
        logger.error(f"Erro ao fechar conexões: {e}")

# =============================================
# UTILITY FUNCTIONS
# =============================================

async def execute_raw_sql(sql: str, params: dict = None):
    """Execute raw SQL query"""
    try:
        async with async_session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result
    except Exception as e:
        logger.error(f"Error executing raw SQL: {e}")
        raise

async def get_table_names() -> list:
    """Get list of all table names"""
    try:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in result.fetchall()]
            return sorted(tables)
    except Exception as e:
        logger.error(f"Error getting table names: {e}")
        return []