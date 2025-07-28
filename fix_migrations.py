#!/usr/bin/env python3
# =============================================
# fix_migrations.py - Corrigir problemas de migração
# =============================================
import os
import shutil

def fix_env_py():
    """Corrigir o arquivo env.py"""
    env_content = '''# migrations/env.py - VERSÃO CORRIGIDA
import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Adicionar projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importações do projeto - TODOS OS MODELOS
try:
    from app.config.database import Base
    from app.config.settings import get_settings
    
    # Importar TODOS os modelos para que sejam detectados pelo Alembic
    from app.database.models.user import User
    from app.database.models.company import Company
    from app.database.models.job import Job
    from app.database.models.curriculum import Curriculum
    from app.database.models.professional_profile import ProfessionalProfile
    from app.database.models.professional_experience import ProfessionalExperience
    from app.database.models.academic_background import AcademicBackground
    from app.database.models.professional_courses import ProfessionalCourses
    from app.database.models.application_job import ApplicationJob
    from app.database.models.analyze_application_job import AnalyzeApplicationJob
    from app.database.models.address import Address
    
    settings = get_settings()
    print("✅ Importações do projeto carregadas com sucesso")
    print(f"📦 Modelos importados: {len(Base.metadata.tables)} tabelas")
    
except ImportError as e:
    print(f"❌ ERRO ao importar: {e}")
    print(f"Diretório atual: {os.getcwd()}")
    raise

# Configuração do Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """Obter URL do banco"""
    # CORREÇÃO: tentar diferentes formas de acessar a URL
    try:
        if hasattr(settings, 'get_database_url'):
            url = settings.get_database_url()
        elif hasattr(settings, 'database_url'):
            url = settings.database_url
        elif hasattr(settings, 'DATABASE_URL'):
            url = settings.DATABASE_URL
        else:
            raise AttributeError("Não foi possível encontrar DATABASE_URL")
        
        print(f"🔗 Database URL obtida com sucesso")
        return url
    except Exception as e:
        print(f"❌ Erro ao obter Database URL: {e}")
        # Fallback para variável de ambiente
        url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:pass@localhost:5432/db')
        print(f"🔗 Usando Database URL do ambiente: {url}")
        return url

def run_migrations_offline() -> None:
    """Executar migrações offline"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Executar migrações com conexão"""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Executar migrações assíncronas"""
    try:
        configuration = config.get_section(config.config_ini_section, {})
        configuration["sqlalchemy.url"] = get_url()
        
        connectable = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()
        print("✅ Migrações executadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro nas migrações: {e}")
        raise

def run_migrations_online() -> None:
    """Executar migrações online"""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    
    # Escrever arquivo
    env_path = "migrations/env.py"
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Arquivo {env_path} corrigido!")

def create_models_init():
    """Criar __init__.py nos modelos"""
    init_content = '''# =============================================
# app/database/models/__init__.py
# =============================================
"""
Database Models Package

Importa todos os modelos para garantir que sejam registrados no SQLAlchemy.
Este arquivo garante que o Alembic detecte todas as tabelas para migrações.
"""

# Importar todos os modelos para registro no Base.metadata
from .user import User
from .company import Company
from .job import Job
from .curriculum import Curriculum
from .professional_profile import ProfessionalProfile
from .professional_experience import ProfessionalExperience
from .academic_background import AcademicBackground
from .professional_courses import ProfessionalCourses
from .application_job import ApplicationJob
from .analyze_application_job import AnalyzeApplicationJob
from .address import Address

# Lista de todos os modelos para fácil acesso
__all__ = [
    "User",
    "Company", 
    "Job",
    "Curriculum",
    "ProfessionalProfile",
    "ProfessionalExperience",
    "AcademicBackground",
    "ProfessionalCourses",
    "ApplicationJob",
    "AnalyzeApplicationJob",
    "Address"
]
'''
    
    # Criar diretório se não existir
    models_dir = "app/database/models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Escrever arquivo
    init_path = f"{models_dir}/__init__.py"
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(init_content)
    
    print(f"✅ Arquivo {init_path} criado!")

def main():
    print("🔧 Corrigindo problemas de migração...")
    
    # Corrigir env.py
    fix_env_py()
    
    # Criar __init__.py nos modelos
    create_models_init()
    
    print("\n✅ Correções aplicadas com sucesso!")
    print("\n📝 Agora execute:")
    print("   python -m alembic revision --autogenerate -m 'Add all models'")
    print("   python -m alembic upgrade head")

if __name__ == "__main__":
    main()
