# migrations/env.py - VERSÃO CORRIGIDA
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

# Importações do projeto
try:
    from app.config.database import Base
    from app.database.models.user import User
    from app.config.settings import settings
    print("✅ Importações do projeto carregadas com sucesso")
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
    url = settings.database_url
    print(f"🔗 Database URL: {url}")
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
