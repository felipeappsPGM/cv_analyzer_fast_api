# 🤖 Resume Analyzer API

Sistema inteligente para análise automatizada de currículos usando Large Language Models (LLM) e LangGraph.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [API Documentation](#-api-documentation)
- [Desenvolvimento](#-desenvolvimento)
- [Deploy](#-deploy)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## 🎯 Visão Geral

O Resume Analyzer é uma plataforma completa que utiliza inteligência artificial para analisar currículos e determinar a compatibilidade entre candidatos e vagas de emprego. O sistema processa automaticamente documentos em diversos formatos (PDF, DOC, DOCX, TXT) e gera análises detalhadas com scores ponderados.

### 🔍 Como Funciona

1. **Cadastro de Vagas**: Recrutadores registram vagas com requisitos específicos
2. **Upload de Currículos**: Candidatos fazem upload de seus currículos
3. **Análise Inteligente**: IA processa e analisa compatibilidade usando LLM
4. **Rankings**: Sistema gera rankings de candidatos por vaga
5. **Relatórios**: Geração de relatórios detalhados em PDF

## ✨ Funcionalidades

### 👥 Gestão de Usuários
- ✅ Sistema de autenticação JWT
- ✅ Múltiplos tipos de usuário (admin, recruiter, candidate)
- ✅ Perfis profissionais completos
- ✅ Histórico de experiências e formação

### 🏢 Gestão Empresarial
- ✅ Cadastro de empresas
- ✅ Gestão de vagas por empresa
- ✅ Dashboard para recrutadores
- ✅ Métricas e analytics

### 💼 Perfis Profissionais
- ✅ Experiência profissional detalhada
- ✅ Formação acadêmica
- ✅ Cursos e certificações
- ✅ Cálculo automático de completude

### 🔍 Análise Inteligente
- ✅ Integração com múltiplos LLMs (OpenAI, Anthropic, Groq, Gemini)
- ✅ Workflow de análise com LangGraph
- ✅ Sistema de pontuação ponderada
- ✅ Identificação de pontos fortes e fracos

### 📊 Sistema de Pontuação

| Critério | Peso | Descrição |
|----------|------|-----------|
| **Experiência Profissional** | 35% | Relevância e tempo de experiência |
| **Formação Acadêmica** | 30% | Nível e área de formação |
| **Cursos Profissionalizantes** | 20% | Certificações e especializações |
| **Pontos Fortes** | +15% | Competências destacadas |
| **Pontos Fracos** | -10% | Áreas de melhoria |

**Fórmula:**
```
Score Final = (Experiência × 0.35) + (Formação × 0.30) + (Cursos × 0.20) + (Pontos Fortes × 0.15) - (Pontos Fracos × 0.10)
```

## 🏗️ Arquitetura

### Stack Tecnológico

#### Backend
- **Framework**: FastAPI 0.104.1
- **Linguagem**: Python 3.11+
- **ORM**: SQLAlchemy (Async)
- **Banco de Dados**: PostgreSQL 15+
- **Migrações**: Alembic
- **Cache**: Redis
- **Message Queue**: RabbitMQ

#### IA e Machine Learning
- **LLM Providers**: OpenAI, Anthropic, Groq, Gemini
- **Workflow Engine**: LangGraph
- **Processamento de Texto**: NLTK, spaCy
- **Análise de Documentos**: PyPDF2, python-docx

#### Infraestrutura
- **Containerização**: Docker & Docker Compose
- **Servidor Web**: Uvicorn/Gunicorn
- **Proxy Reverso**: Nginx
- **Monitoramento**: Prometheus, Grafana

### Diagramas de Arquitetura

```mermaid
graph TB
    subgraph "Frontend"
        UI[Web Interface]
        API_CLIENT[API Client]
    end
    
    subgraph "Backend"
        GATEWAY[API Gateway]
        AUTH[Authentication]
        SERVICES[Business Services]
        REPOS[Repositories]
    end
    
    subgraph "AI/ML"
        LLM[LLM Providers]
        LANGGRAPH[LangGraph]
        ANALYSIS[Analysis Engine]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        RABBITMQ[RabbitMQ]
    end
    
    UI --> API_CLIENT
    API_CLIENT --> GATEWAY
    GATEWAY --> AUTH
    GATEWAY --> SERVICES
    SERVICES --> REPOS
    REPOS --> POSTGRES
    SERVICES --> REDIS
    SERVICES --> RABBITMQ
    SERVICES --> ANALYSIS
    ANALYSIS --> LANGGRAPH
    LANGGRAPH --> LLM
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (ou usar Docker)
- Redis (ou usar Docker)
- Git

### Instalação Rápida

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/resume-analyzer-api.git
   cd resume-analyzer-api
   ```

2. **Execute o script de setup**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure as variáveis de ambiente**:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. **Inicie os serviços**:
   ```bash
   docker-compose up -d
   ```

### Instalação Manual

<details>
<summary>Clique para ver instalação manual</summary>

1. **Criar ambiente virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar banco de dados**:
   ```bash
   # Inicie PostgreSQL via Docker
   docker run -d --name postgres \
     -e POSTGRES_DB=resume_analyzer \
     -e POSTGRES_USER=resume_user \
     -e POSTGRES_PASSWORD=resume_password \
     -p 5432:5432 postgres:15-alpine
   ```

4. **Executar migrações**:
   ```bash
   alembic upgrade head
   ```

5. **Iniciar aplicação**:
   ```bash
   uvicorn app.main:app --reload
   ```

</details>

## ⚙️ Configuração

### Variáveis de Ambiente Essenciais

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/resume_analyzer

# Security
SECRET_KEY=your-super-secret-key-minimum-64-characters
ALGORITHM=HS256

# LLM APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk_your-groq-key
GEMINI_API_KEY=your-gemini-key

# Cache & Queue
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://user:pass@localhost:5672/
```

### Configuração de LLM

O sistema suporta múltiplos provedores de LLM:

| Provedor | Modelo Padrão | Configuração |
|----------|---------------|--------------|
| **OpenAI** | gpt-4-1106-preview | `OPENAI_API_KEY` |
| **Anthropic** | claude-3-sonnet | `ANTHROPIC_API_KEY` |
| **Groq** | mixtral-8x7b-32768 | `GROQ_API_KEY` |
| **Gemini** | gemini-pro | `GEMINI_API_KEY` |

## 📖 Uso

### Comandos de Manutenção

O sistema inclui um script de manutenção completo:

```bash
# Setup inicial do banco
python scripts/maintenance.py db-setup

# Criar usuário administrador
python scripts/maintenance.py user-create

# Backup do banco
python scripts/maintenance.py db-backup

# Health check completo
python scripts/maintenance.py health-check

# Limpeza de arquivos antigos
python scripts/maintenance.py cleanup --days 30

# Popular com dados de exemplo
python scripts/maintenance.py seed-data
```

### Exemplos de Uso da API

#### Criar Usuário
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "João Silva",
    "user_email": "joao@email.com",
    "password": "MinhaSenh@123",
    "user_type": "candidate"
  }'
```

#### Upload de Currículo
```bash
curl -X POST "http://localhost:8000/api/v1/curriculum/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@curriculo.pdf"
```

#### Criar Vaga
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Desenvolvedor Python Sênior",
    "activities": "Desenvolvimento de APIs em Python",
    "pre_requisites": "5+ anos Python, Django, PostgreSQL",
    "company_id": "uuid-da-empresa"
  }'
```

## 📚 API Documentation

### Endpoints Principais

| Grupo | Endpoint | Descrição |
|-------|----------|-----------|
| **Auth** | `POST /api/v1/auth/login` | Autenticação |
| **Users** | `GET /api/v1/users/` | Listar usuários |
| **Jobs** | `GET /api/v1/jobs/` | Listar vagas |
| **Applications** | `POST /api/v1/applications/` | Candidatar-se |
| **Analysis** | `GET /api/v1/analysis/{id}` | Resultado da análise |

### Documentação Interativa

Acesse a documentação interativa:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Códigos de Status

| Código | Descrição |
|--------|-----------|
| `200` | Sucesso |
| `201` | Criado com sucesso |
| `400` | Erro de validação |
| `401` | Não autenticado |
| `403` | Sem permissão |
| `404` | Não encontrado |
| `422` | Erro de validação Pydantic |
| `500` | Erro interno |

## 🔧 Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

1. **Instalar dependências de desenvolvimento**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Executar testes**:
   ```bash
   pytest
   pytest --cov=app  # Com coverage
   ```

4. **Formatar código**:
   ```bash
   black .
   isort .
   flake8 .
   ```

### Estrutura do Projeto

```
resume-analyzer-api/
├── app/                          # Código da aplicação
│   ├── api/                      # Endpoints da API
│   │   └── v1/
│   │       ├── endpoints/        # Rotas específicas
│   │       └── router.py
│   ├── config/                   # Configurações
│   │   ├── database.py
│   │   └── settings.py
│   ├── core/                     # Núcleo da aplicação
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── database/                 # Modelos do banco
│   │   └── models/
│   ├── repositories/             # Camada de dados
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Lógica de negócio
│   └── main.py
├── migrations/                   # Migrações Alembic
├── scripts/                      # Scripts de utilidade
├── tests/                        # Testes
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Workflow de Desenvolvimento

1. **Criar branch para feature**:
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

2. **Desenvolver e testar**:
   ```bash
   # Fazer alterações
   pytest  # Executar testes
   black . # Formatar código
   ```

3. **Commit e push**:
   ```bash
   git add .
   git commit -m "feat: adicionar nova funcionalidade"
   git push origin feature/nova-funcionalidade
   ```

4. **Criar Pull Request**

### Executando Testes

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_services/

# Com coverage
pytest --cov=app --cov-report=html

# Testes de integração
pytest tests/integration/

# Testes em paralelo
pytest -n auto
```

## 🚢 Deploy

### Deploy Local (Docker)

```bash
# Build e start
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f api
```

### Deploy em Produção

<details>
<summary>Deploy com Docker Swarm</summary>

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml resume-analyzer

# Verificar serviços
docker service ls
```

</details>

<details>
<summary>Deploy no Kubernetes</summary>

```bash
# Aplicar manifests
kubectl apply -f k8s/

# Verificar status
kubectl get pods -n resume-analyzer

# Acompanhar logs
kubectl logs -f deployment/resume-analyzer-api
```

</details>

### Variáveis de Ambiente Produção

```env
# Produção
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Security
SECRET_KEY=production-secret-key-64-characters-minimum
ALLOWED_HOSTS=https://yourdomain.com

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/resume_analyzer

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

## 🧪 Testes

### Tipos de Teste

- **Unit Tests**: Testam componentes isolados
- **Integration Tests**: Testam integração entre componentes
- **E2E Tests**: Testam fluxos completos
- **Performance Tests**: Testam performance da API

### Executar Suíte Completa

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Testes E2E
pytest tests/e2e/

# Coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 📊 Monitoramento

### Métricas Disponíveis

- **API Metrics**: Latência, throughput, erro rate
- **Database Metrics**: Conexões, queries, performance
- **LLM Metrics**: Uso de tokens, custos, latência
- **Business Metrics**: Análises processadas, usuários ativos

### Health Checks

```bash
# Health check da API
curl http://localhost:8000/api/v1/health

# Health check completo
python scripts/maintenance.py health-check
```

### Logs

```bash
# Ver logs da aplicação
tail -f logs/app.log

# Logs do Docker
docker-compose logs -f api

# Logs estruturados
grep "level=ERROR" logs/app.log | jq .
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork o projeto**
2. **Criar branch para feature** (`git checkout -b feature/AmazingFeature`)
3. **Commit suas mudanças** (`git commit -m 'Add some AmazingFeature'`)
4. **Push para a branch** (`git push origin feature/AmazingFeature`)
5. **Abrir Pull Request**

### Diretrizes

- Seguir o padrão de código (Black, isort, flake8)
- Escrever testes para novas funcionalidades
- Documentar mudanças no código
- Atualizar documentação se necessário

### Reportar Issues

Use as [GitHub Issues](https://github.com/seu-usuario/resume-analyzer-api/issues) para:

- 🐛 Reportar bugs
- 💡 Sugerir features
- 📝 Melhorias na documentação
- ❓ Fazer perguntas

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Email**: support@resume-analyzer.com
- **Discord**: [Resume Analyzer Community](https://discord.gg/resume-analyzer)
- **GitHub Issues**: [Issues](https://github.com/seu-usuario/resume-analyzer-api/issues)
- **Documentation**: [Wiki](https://github.com/seu-usuario/resume-analyzer-api/wiki)

## 🙏 Agradecimentos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [LangChain](https://langchain.com/) - Framework para LLM
- [PostgreSQL](https://www.postgresql.org/) - Banco de dados
- [Docker](https://www.docker.com/) - Containerização

---

**Status do Projeto**: 🟢 Em Desenvolvimento Ativo

**Última Atualização**: Janeiro 2025

**Versão**: 1.0.0