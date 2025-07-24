# =============================================
# debug_database.py - Script para diagnosticar problemas de conexão
# =============================================
import asyncio
import sys
import os
from pathlib import Path
import asyncpg
# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

async def test_database_connection():
    """Testar conexão com banco de dados"""
    print("🔍 DIAGNÓSTICO DE BANCO DE DADOS")
    print("=" * 50)
    
    # 1. Verificar se .env existe
    print("1. Verificando arquivo .env...")
    if os.path.exists(".env"):
        print("   ✅ Arquivo .env encontrado")
    else:
        print("   ❌ Arquivo .env NÃO encontrado")
        print("   💡 Copie .env.example para .env")
        return False
    
    # 2. Verificar imports básicos
    print("\n2. Verificando imports...")
    try:
        from app.config.settings import settings
        print("   ✅ Settings importado com sucesso")
        print(f"   📋 DATABASE_URL: {settings.database_url}")
    except Exception as e:
        print(f"   ❌ Erro ao importar settings: {e}")
        return False
    
    try:
        import asyncpg
        print("   ✅ AsyncPG instalado")
    except ImportError:
        print("   ❌ AsyncPG NÃO instalado")
        print("   💡 Execute: pip install asyncpg")
        return False
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        print("   ✅ SQLAlchemy async disponível")
    except ImportError:
        print("   ❌ SQLAlchemy async NÃO disponível")
        return False
    
    # 3. Testar conexão direta
    print("\n3. Testando conexão direta com PostgreSQL...")
    try:
        # Extrair dados da URL
        url_parts = settings.database_url.replace("postgresql+asyncpg://", "").split("@")
        user_pass = url_parts[0]
        host_db = url_parts[1]
        
        user = user_pass.split(":")[0]
        password = user_pass.split(":")[1]
        host = host_db.split(":")[0]
        port_db = host_db.split(":")[1]
        port = port_db.split("/")[0]
        database = port_db.split("/")[1]
        
        print(f"   📡 Tentando conectar em: {host}:{port}/{database}")
        print(f"   👤 Usuário: {user}")
        
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        
        # Teste simples
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        print("   ✅ Conexão direta FUNCIONANDO")
        print(f"   📊 Teste query result: {result}")
        
    except Exception as e:
        print(f"   ❌ Erro na conexão direta: {e}")
        print("   💡 Verifique se o PostgreSQL está rodando")
        print("   💡 Execute: docker-compose up -d")
        return False
    
    # 4. Testar SQLAlchemy async
    print("\n4. Testando SQLAlchemy async...")
    try:
        engine = create_async_engine(settings.database_url)
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            value = result.scalar()
            
        await engine.dispose()
        print("   ✅ SQLAlchemy async FUNCIONANDO")
        print(f"   📊 Teste query result: {value}")
        
    except Exception as e:
        print(f"   ❌ Erro no SQLAlchemy async: {e}")
        return False
    
    # 5. Verificar modelos
    print("\n5. Verificando modelos...")
    try:
        from app.database.models.user import User
        from app.config.database import Base
        print("   ✅ Modelos importados com sucesso")
        print(f"   📋 Tabelas detectadas: {list(Base.metadata.tables.keys())}")
    except Exception as e:
        print(f"   ❌ Erro ao importar modelos: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 DIAGNÓSTICO CONCLUÍDO - TUDO OK!")
    print("✅ Banco de dados pronto para Alembic")
    return True

async def test_alembic_config():
    """Testar configuração do Alembic"""
    print("\n🔧 TESTANDO CONFIGURAÇÃO ALEMBIC")
    print("=" * 50)
    
    # Verificar arquivos
    files_to_check = [
        "alembic.ini",
        "migrations/env.py",
        "migrations/script.py.mako"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} existe")
        else:
            print(f"❌ {file_path} NÃO existe")
    
    # Verificar conteúdo do env.py
    print(f"\n📄 Verificando migrations/env.py...")
    try:
        with open("migrations/env.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "from app.config.database import Base" in content:
            print("✅ env.py configurado para o projeto")
        else:
            print("❌ env.py usando configuração padrão")
            print("💡 Substitua o conteúdo pelo env.py correto")
            
    except Exception as e:
        print(f"❌ Erro ao ler env.py: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO DIAGNÓSTICO...")
    
    # Executar testes
    asyncio.run(test_database_connection())
    asyncio.run(test_alembic_config())
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Corrigir problemas encontrados acima")
    print("2. Substituir migrations/env.py pelo correto")
    print("3. Executar: python -m alembic revision --autogenerate -m 'Initial'")
    print("4. Executar: python -m alembic upgrade head")