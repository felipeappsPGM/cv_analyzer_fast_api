#!/usr/bin/env python3
# =============================================
# fix_all_errors.py - Corrige TODOS os problemas automaticamente
# =============================================
import os
import shutil
from pathlib import Path

def backup_files():
    """Criar backup dos arquivos originais"""
    print("📦 Criando backups...")
    
    files_to_backup = [
        "alembic.ini",
        "migrations/env.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            shutil.copy(file_path, backup_path)
            print(f"   ✅ Backup: {backup_path}")

def fix_alembic_ini():
    """Criar alembic.ini simplificado e funcional"""
    print("🔧 Corrigindo alembic.ini...")
    
    simple_ini_content = """[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://username:password@localhost:5432/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
    
    with open("alembic.ini", "w", encoding="utf-8") as f:
        f.write(simple_ini_content)
    
    print("   ✅ alembic.ini reescrito (versão simplificada)")

def fix_migrations_env():
    """Criar env.py corrigido e funcional"""
    print("🔧 Corrigindo migrations/env.py...")
    
    corrected_env_content = '''# migrations/env.py - VERSÃO CORRIGIDA
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
'''
    
    env_path = Path("migrations/env.py")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(corrected_env_content)
    
    print("   ✅ migrations/env.py reescrito (versão corrigida)")

def test_configuration():
    """Testar se as configurações estão funcionando"""
    print("🧪 Testando configurações...")
    
    try:
        from app.config.settings import settings
        print(f"   ✅ Settings carregado: {settings.database_url}")
    except Exception as e:
        print(f"   ❌ Erro no settings: {e}")
        return False
    
    try:
        from app.config.database import Base
        from app.database.models.user import User
        print("   ✅ Modelos carregados")
    except Exception as e:
        print(f"   ❌ Erro nos modelos: {e}")
        return False
    
    return True

def show_next_steps():
    """Mostrar próximos passos"""
    print("\n" + "=" * 50)
    print("🎉 CORREÇÕES APLICADAS COM SUCESSO!")
    print("=" * 50)
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1️⃣  Subir banco: docker-compose up -d")
    print("2️⃣  Gerar migração: python -m alembic revision --autogenerate -m 'Create users table'")
    print("3️⃣  Aplicar migração: python -m alembic upgrade head")
    print("4️⃣  Iniciar API: python -m uvicorn app.main:app --reload")
    print("\n🌐 Após iniciar, acesse:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    print("\n💾 Backups criados:")
    print("   • alembic.ini.backup")
    print("   • migrations/env.py.backup")

def main():
    print("🚀 CORREÇÃO AUTOMÁTICA DE TODOS OS ERROS")
    print("=" * 50)
    
    # 1. Criar backups
    backup_files()
    
    # 2. Corrigir alembic.ini
    fix_alembic_ini()
    
    # 3. Corrigir migrations/env.py
    fix_migrations_env()
    
    # 4. Testar configurações
    if test_configuration():
        show_next_steps()
    else:
        print("\n❌ ERRO: Problemas encontrados nas configurações")
        print("💡 Verifique se está no diretório correto do projeto")
        print("💡 Verifique se o arquivo .env existe")

if __name__ == "__main__":
    main()