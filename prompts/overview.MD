# 📋 Sistema de Análise de Currículos com LLM - Guia de Setup Completo

## 📖 Visão Geral

Sistema inteligente para análise automatizada de currículos usando Large Language Models (LLM) e LangGraph. Permite que recrutadores registrem vagas, candidatos enviem currículos e recebam análises de compatibilidade automatizadas.

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico
- **Backend**: FastAPI + Python 3.11+
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Banco de Dados**: PostgreSQL 15+
- **IA/ML**: LangGraph + LLM APIs (OpenAI, Anthropic, Groq, Gemini)
- **Message Queue**: RabbitMQ
- **ORM**: SQLAlchemy (Async)
- **Migrations**: Alembic
- **Containerização**: Docker + Docker Compose

### Usuários do Sistema
- **Recruiters**: Cadastram vagas e visualizam análises
- **HR Analysts**: Analisam relatórios e rankings
- **Candidates**: Cadastram perfis e se candidatam
- **Company Owners**: Gerenciam empresas e equipes

## 🚀 Setup do Ambiente

### 1. Pré-requisitos

```bash
# Instalar dependências do sistema
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
```

### 2. Clonagem e Configuração Inicial

```bash
# Clonar repositório
git clone <repository-url>
cd resume-analyzer-system

# Criar ambiente virtual Python
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências Python
pip install -r requirements.txt
```

### 3. Configuração de Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
```

**Arquivo .env:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/resume_analyzer
DATABASE_URL_SYNC=postgresql://username:password@localhost:5432/resume_analyzer

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
GEMINI_API_KEY=your-gemini-key

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# App
APP_NAME=Resume Analyzer System
DEBUG=True
VERSION=1.0.0
```

### 4. Inicialização dos Serviços

```bash
# Subir banco de dados e RabbitMQ
docker-compose up -d

# Verificar se serviços estão rodando
docker-compose ps
```

### 5. Configuração do Banco de Dados

```bash
# Executar migrações
python -m alembic upgrade head

# Verificar tabelas criadas
python debug_database.py
```

### 6. Instalação do Frontend

```bash
# Navegar para diretório frontend
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente frontend
cp .env.local.example .env.local
```

**Frontend .env.local:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Resume Analyzer
```

## 🗄️ Estrutura de Diretórios

```
resume-analyzer-system/
├── app/                          # Backend FastAPI
│   ├── api/                      # Endpoints da API
│   │   └── v1/
│   │       ├── endpoints/        # Rotas específicas
│   │       └── router.py
│   ├── config/                   # Configurações
│   │   ├── database.py
│   │   └── settings.py
│   ├── core/                     # Núcleo da aplicação
│   │   ├── auth.py
│   │   ├── exceptions.py
│   │   ├── security.py
│   │   └── validators.py
│   ├── database/                 # Modelos do banco
│   │   └── models/
│   ├── repositories/             # Camada de dados
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Lógica de negócio
│   │   ├── llm_service.py
│   │   ├── analysis_service.py
│   │   └── user_service.py
│   └── main.py
├── frontend/                     # Frontend Next.js
│   ├── components/               # Componentes React
│   ├── pages/                    # Páginas Next.js
│   ├── styles/                   # Estilos Tailwind
│   ├── lib/                      # Utilities
│   └── types/                    # TypeScript types
├── migrations/                   # Migrações Alembic
├── docs/                         # Documentação
├── tests/                        # Testes
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 Modelos de Dados (Entidades)

### Entidades Principais

```python
# Principais entidades do sistema:
- Users (Usuários)
- Company (Empresas)
- Job (Vagas)
- Curriculum (Currículos)
- ProfessionalProfile (Perfil Profissional)
- ProfessionalExperience (Experiência)
- AcademicBackground (Formação)
- ProfessionalCourses (Cursos)
- ApplicationJob (Candidaturas)
- AnalyzeApplicationJob (Análises)
- Address (Endereços)
```

## 🔄 Executando o Sistema

### 1. Backend (FastAPI)

```bash
# Desenvolvimento
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verificar se está funcionando
curl http://localhost:8000/health
```

### 2. Frontend (Next.js)

```bash
cd frontend
npm run dev
```

### 3. Verificar Integração

```bash
# Acessar aplicação
http://localhost:3000         # Frontend
http://localhost:8000         # Backend API
http://localhost:8000/docs    # Swagger Documentation
http://localhost:5050         # PgAdmin (se configurado)
```

## 🧪 Testes

```bash
# Executar testes backend
python -m pytest tests/ -v

# Executar testes frontend
cd frontend
npm run test

# Testes de integração
python -m pytest tests/integration/ -v
```

## 📝 Scripts Úteis

```bash
# Resetar banco de dados
python -m alembic downgrade base
python -m alembic upgrade head

# Gerar nova migração
python -m alembic revision --autogenerate -m "Description"

# Debugar configuração
python debug_database.py

# Corrigir problemas automaticamente
python fix_all_errors.py
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco:**
   ```bash
   # Verificar se PostgreSQL está rodando
   docker-compose ps
   
   # Reiniciar serviços
   docker-compose restart postgres
   ```

2. **Erro nas migrações:**
   ```bash
   # Corrigir automaticamente
   python fix_all_errors.py
   ```

3. **Problemas com LLM APIs:**
   ```bash
   # Verificar chaves de API no .env
   # Testar conectividade
   python test_llm_connection.py
   ```

## 🚢 Deploy em Produção

### Preparação

```bash
# Build da aplicação
cd frontend
npm run build

# Configurar variáveis de produção
cp .env.example .env.production
```

### Docker Production

```bash
# Build imagens
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Documentação Adicional

- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [Postman Collection](./FastAPI_Users_Collection.json) - Testes de API
- [Database Schema](./docs/database-schema.md) - Esquema do banco
- [Business Rules](./docs/business-rules.md) - Regras de negócio

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

Para suporte, envie um email para support@resume-analyzer.com ou abra uma issue no GitHub.

---

**Status do Projeto:** 🟢 Em Desenvolvimento Ativo

**Última Atualização:** Janeiro 2025