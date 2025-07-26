# 🤖 Guia de Prompts para IA - Sistema de Análise de Currículos

## 📋 Instruções Gerais

Este documento contém prompts estruturados para gerar automaticamente todo o código do sistema baseado no DER e especificações. Use cada prompt sequencialmente para criar uma aplicação completa.

## 🗄️ 1. CRIAÇÃO DOS MODELOS DO BANCO DE DADOS

### 📝 Prompt: Gerar Modelos SQLAlchemy

```
Crie os modelos SQLAlchemy para um sistema de análise de currículos com LLM. Baseie-se no seguinte DER:

ENTIDADES:
- Users: user_id(PK), user_name, user_email(UK), password, is_work, user_type, birth_day, professional_profile_id(FK), professional_experience_id(FK), professional_courses_id(FK), academic_background_id(FK), analyze_application_job_id(FK), curriculum_id(FK), address_id(FK), company_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- Company: company_id(PK), company_name, area_of_activity, cnpj(UK), address_id(FK), job_id(FK), user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- Job: job_id(PK), job_name, activities, pre_requisites, differentials, company_id(FK), code_vacancy_job(UK), created_date, updated_date, deleted_date, create_user_id(FK)

- ProfessionalProfile: professional_profile_id(PK), professional_profile_name, professional_profile_description, academic_background_id(FK), professional_experience_id(FK), professional_courses_id(FK), user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- ProfessionalExperience: professional_experience_id(PK), job_title, company_name, employment_type, location, start_date, end_date, is_current, user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- AcademicBackground: academic_background_id(PK), degree_name, degree_type, field_of_study, institution_name, start_date, end_date, user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- ProfessionalCourses: professional_courses_id(PK), course_name, institution_name, token_id, duration_time_hours, certification_media_pdf, certification_media_image, start_date, end_date, user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- Curriculum: curriculum_id(PK), file_base64, file_path, file_name(UK), is_work, user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- ApplicationJob: application_job_id(PK), professional_profile_id(FK), job_id(FK), user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- AnalyzeApplicationJob: analyze_application_job_id(PK), professional_profile_id(FK), academic_score, professional_experience_score, professional_courses_score, weak_points_score, strong_points_score, total_score, opinion_application_job, user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

- Address: address_id(PK), street_type, street_name, number, cep, neighborhood, cidade, city, state, country, company_id(FK), user_id(FK), created_date, updated_date, deleted_date, create_user_id(FK)

REQUISITOS:
- Use UUID para todas as chaves primárias
- Implemente soft delete com deleted_date
- Use timezone-aware datetime
- Estabeleça relacionamentos FK apropriados
- Adicione índices para performance
- Use SQLAlchemy async
- Implemente validações básicas
- Adicione metadados de auditoria

Crie cada modelo em arquivo separado na estrutura: app/database/models/[entidade].py
```

### 📝 Prompt: Gerar Schemas Pydantic

```
Crie os schemas Pydantic para validação de dados baseados nos modelos SQLAlchemy criados anteriormente.

Para cada entidade, crie:
1. Schema Base (campos comuns)
2. Schema Create (para criação)
3. Schema Update (para atualização, campos opcionais)
4. Schema Response (para retorno da API, sem dados sensíveis)
5. Schema Detail (com relacionamentos carregados)

REGRAS:
- Use EmailStr para emails
- Implemente validações customizadas (senhas, CPF/CNPJ, etc.)
- Configure model_config = ConfigDict(from_attributes=True)
- Use Field() para validações e documentação
- Exclua campos sensíveis (password) dos schemas de response
- Implemente validações de negócio (datas, scores, etc.)

VALIDAÇÕES ESPECÍFICAS:
- Password: mínimo 8 caracteres, maiúscula, minúscula, número
- Email: formato válido e único
- Scores: entre 0 e 100
- Datas: lógica de início/fim
- Arquivos: tipos permitidos, tamanho máximo

Estrutura: app/schemas/[entidade].py
```

## 🔧 2. CRIAÇÃO DA CAMADA DE REPOSITÓRIOS

### 📝 Prompt: Gerar Repositórios de Dados

```
Crie repositórios para acesso aos dados seguindo o padrão Repository Pattern.

Para cada entidade, implemente:

MÉTODOS BÁSICOS CRUD:
- create(entity_data) -> Entity
- get_by_id(entity_id) -> Optional[Entity]
- get_all(skip, limit) -> List[Entity]
- update(entity_id, update_data) -> Optional[Entity]
- soft_delete(entity_id) -> bool

MÉTODOS ESPECÍFICOS POR ENTIDADE:

UserRepository:
- get_by_email(email) -> Optional[User]
- get_by_user_type(user_type) -> List[User]
- get_active_users() -> List[User]

CompanyRepository:
- get_by_cnpj(cnpj) -> Optional[Company]
- get_companies_with_jobs() -> List[Company]

JobRepository:
- get_by_company(company_id) -> List[Job]
- get_active_jobs() -> List[Job]
- search_jobs(keywords) -> List[Job]

ApplicationJobRepository:
- get_by_job(job_id) -> List[ApplicationJob]
- get_by_user(user_id) -> List[ApplicationJob]
- check_user_applied(user_id, job_id) -> bool

AnalyzeApplicationJobRepository:
- get_by_job_ranked(job_id) -> List[AnalyzeApplicationJob]
- get_top_candidates(job_id, limit) -> List[AnalyzeApplicationJob]
- get_analysis_stats(job_id) -> Dict

REQUISITOS:
- Use SQLAlchemy async
- Implemente filtros de soft delete em todas as queries
- Adicione tratamento de erros
- Use transações quando necessário
- Implemente paginação
- Adicione logging
- Use type hints

Estrutura: app/repositories/[entidade]_repository.py
```

## ⚙️ 3. CRIAÇÃO DA CAMADA DE SERVIÇOS

### 📝 Prompt: Gerar Serviços de Negócio

```
Crie a camada de serviços que implementa a lógica de negócio do sistema.

SERVIÇOS PRINCIPAIS:

UserService:
- create_user(user_data) -> UserResponse
- authenticate_user(email, password) -> Optional[User]
- get_user_profile(user_id) -> UserDetail
- update_user_profile(user_id, update_data) -> UserDetail

CompanyService:
- create_company(company_data) -> CompanyResponse
- get_company_details(company_id) -> CompanyDetail
- add_user_to_company(company_id, user_id) -> bool

JobService:
- create_job(job_data) -> JobResponse
- get_job_details(job_id) -> JobDetail
- search_jobs(filters) -> List[JobResponse]
- close_job(job_id) -> bool

ApplicationService:
- apply_to_job(user_id, job_id) -> ApplicationResponse
- get_user_applications(user_id) -> List[ApplicationResponse]
- get_job_applications(job_id) -> List[ApplicationResponse]

AnalysisService:
- analyze_application(application_id) -> AnalyzeApplicationJobResponse
- get_job_ranking(job_id) -> List[RankingResponse]
- generate_analysis_report(job_id) -> bytes (PDF)
- calculate_compatibility_score(profile, job) -> float

LLMService:
- extract_resume_data(resume_content) -> Dict
- analyze_compatibility(resume_data, job_description) -> AnalysisResult
- generate_feedback(analysis_result) -> str

REGRAS DE NEGÓCIO A IMPLEMENTAR:
- BR01-BR06: Sistema de pontuação ponderada
- BR07: Permitir registro sem perfil completo
- BR08: Uma aplicação por usuário por vaga
- Validações de permissões por user_type
- Logs de auditoria
- Tratamento de exceções customizadas

INTEGRAÇÃO COM LLM:
- Use LangGraph para workflow de análise
- Implemente retry e fallback
- Monitore custos de API
- Cache resultados quando possível

Estrutura: app/services/[entidade]_service.py
```

### 📝 Prompt: Gerar Serviço de LLM e LangGraph

```
Crie um serviço especializado para integração com LLM e LangGraph para análise de currículos.

FUNCIONALIDADES:

LLMService:
- Configuração para múltiplos providers (OpenAI, Anthropic, Groq, Gemini)
- Extração de dados de currículos (PDF, DOC, TXT)
- Análise de compatibilidade currículo-vaga
- Geração de feedback explicativo

LangGraphWorkflow:
- Nó 1: Extração de dados do currículo
- Nó 2: Normalização e estruturação
- Nó 3: Análise de experiência profissional (35%)
- Nó 4: Análise de formação acadêmica (30%)
- Nó 5: Análise de cursos profissionalizantes (20%)
- Nó 6: Identificação de pontos fortes (15%)
- Nó 7: Identificação de pontos fracos (-10%)
- Nó 8: Cálculo de score final
- Nó 9: Geração de opinião textual

PROMPTS PARA LLM:
- Prompt para extração de dados
- Prompt para análise de compatibilidade
- Prompt para geração de feedback
- Prompt para identificação de skills

CONFIGURAÇÕES:
- Timeout e retry automático
- Rate limiting
- Monitoring de custos
- Fallback entre providers
- Cache inteligente

ESTRUTURA:
```python
class LLMService:
    async def extract_resume_data(self, file_content: bytes) -> Dict
    async def analyze_compatibility(self, resume_data: Dict, job_data: Dict) -> AnalysisResult
    async def generate_feedback(self, analysis: AnalysisResult) -> str

class LangGraphAnalyzer:
    def create_workflow(self) -> StateGraph
    async def run_analysis(self, resume_content: str, job_description: str) -> AnalysisResult
```

Implemente com error handling robusto e monitoramento.
Estrutura: app/services/llm_service.py
```

## 🌐 4. CRIAÇÃO DAS APIs

### 📝 Prompt: Gerar Endpoints FastAPI

```
Crie todos os endpoints da API REST seguindo as melhores práticas do FastAPI.

ESTRUTURA DE ENDPOINTS:

/api/v1/auth:
- POST /login - Autenticação
- POST /logout - Logout
- POST /refresh - Refresh token
- POST /forgot-password - Recuperar senha

/api/v1/users:
- POST / - Criar usuário
- GET / - Listar usuários (paginado)
- GET /{user_id} - Obter usuário
- PUT /{user_id} - Atualizar usuário
- DELETE /{user_id} - Deletar usuário (soft)
- GET /{user_id}/profile - Obter perfil completo

/api/v1/companies:
- POST / - Criar empresa
- GET / - Listar empresas
- GET /{company_id} - Obter empresa
- PUT /{company_id} - Atualizar empresa
- POST /{company_id}/users - Adicionar usuário à empresa

/api/v1/jobs:
- POST / - Criar vaga
- GET / - Listar vagas (com filtros)
- GET /{job_id} - Obter vaga
- PUT /{job_id} - Atualizar vaga
- DELETE /{job_id} - Fechar vaga
- GET /{job_id}/applications - Listar candidaturas
- GET /{job_id}/ranking - Ranking de candidatos

/api/v1/applications:
- POST / - Candidatar-se a vaga
- GET /user/{user_id} - Candidaturas do usuário
- GET /{application_id} - Detalhes da candidatura
- DELETE /{application_id} - Cancelar candidatura

/api/v1/analysis:
- POST /analyze/{application_id} - Executar análise
- GET /{analysis_id} - Obter resultado
- GET /job/{job_id}/report - Gerar relatório PDF
- GET /stats/{job_id} - Estatísticas da vaga

/api/v1/curriculum:
- POST /upload - Upload de currículo
- GET /{curriculum_id} - Download currículo
- PUT /{curriculum_id} - Atualizar currículo
- DELETE /{curriculum_id} - Deletar currículo

PADRÕES A SEGUIR:
- Status codes apropriados (200, 201, 204, 400, 401, 403, 404, 409, 500)
- Documentação OpenAPI completa
- Validação de entrada
- Paginação para listagens
- Filtros e ordenação
- Rate limiting
- CORS configurado
- Middleware de logging
- Tratamento de erros global
- Autenticação JWT
- Autorização baseada em roles

MIDDLEWARES:
- Authentication middleware
- CORS middleware
- Logging middleware
- Rate limiting middleware
- Exception handling middleware

Estrutura: app/api/v1/endpoints/[entidade].py
```

### 📝 Prompt: Gerar Sistema de Autenticação

```
Crie um sistema completo de autenticação e autorização.

COMPONENTES:

AuthService:
- login(email, password) -> TokenResponse
- refresh_token(refresh_token) -> TokenResponse  
- forgot_password(email) -> bool
- reset_password(token, new_password) -> bool
- verify_token(token) -> Optional[User]

JWTManager:
- create_access_token(user_data) -> str
- create_refresh_token(user_data) -> str
- verify_token(token) -> Dict
- get_token_data(token) -> TokenData

PermissionService:
- check_permission(user, resource, action) -> bool
- get_user_permissions(user) -> List[Permission]

MIDDLEWARES:
- AuthenticationMiddleware: Validar JWT em rotas protegidas
- AuthorizationMiddleware: Verificar permissões

ROLES E PERMISSÕES:
- admin: Todas as permissões
- company_owner: Gerenciar empresa e vagas
- recruiter: Visualizar candidatos e análises
- candidate: Candidatar-se e ver próprias candidaturas

DECORATORS:
- @require_auth: Exigir autenticação
- @require_role(role): Exigir role específica
- @require_permission(permission): Exigir permissão específica

SCHEMAS:
- LoginRequest: email, password
- TokenResponse: access_token, refresh_token, token_type
- UserClaims: user_id, email, roles, permissions

SEGURANÇA:
- Hash de senhas com bcrypt
- Tokens com expiração
- Blacklist de tokens
- Rate limiting no login
- Bloqueio após tentativas falhadas

Estrutura: app/core/auth.py, app/core/security.py
```

## 🎨 5. CRIAÇÃO DO FRONTEND

### 📝 Prompt: Gerar Frontend Next.js

```
Crie uma aplicação frontend completa em Next.js com TypeScript e Tailwind CSS.

ESTRUTURA DE PÁGINAS:

/auth:
- /login - Página de login
- /register - Página de registro
- /forgot-password - Recuperar senha

/dashboard:
- / - Dashboard principal (diferente por tipo de usuário)
- /profile - Perfil do usuário
- /settings - Configurações

/jobs (para candidatos):
- / - Lista de vagas disponíveis
- /[jobId] - Detalhes da vaga
- /applications - Minhas candidaturas

/company (para empresas):
- / - Dashboard da empresa
- /jobs - Gerenciar vagas
- /jobs/new - Criar nova vaga
- /jobs/[jobId] - Detalhes e candidatos da vaga
- /analytics - Relatórios e métricas

/recruiter (para recrutadores):
- /jobs - Vagas que gerencio
- /jobs/[jobId]/candidates - Ranking de candidatos
- /analytics - Dashboards de métricas

COMPONENTES PRINCIPAIS:

Layout:
- Header com navegação
- Sidebar para navegação interna
- Footer
- Loading states
- Error boundaries

Forms:
- JobForm - Criar/editar vagas
- ProfileForm - Editar perfil
- ApplicationForm - Candidatar-se
- LoginForm/RegisterForm

Tables:
- JobsList - Lista de vagas
- CandidatesList - Lista de candidatos
- ApplicationsList - Lista de candidaturas
- RankingTable - Ranking com scores

Cards:
- JobCard - Cartão de vaga
- CandidateCard - Cartão de candidato
- StatsCard - Cartão de estatísticas
- AnalysisCard - Resultado de análise

Modals:
- ConfirmationModal
- FileUploadModal
- AnalysisResultModal

FUNCIONALIDADES:
- Autenticação com contexto
- Upload de arquivos
- Filtros e busca
- Paginação
- Sorting
- Real-time updates (WebSocket)
- Notificações toast
- Loading skeletons
- Error handling
- Responsive design

ESTADO E DATA:
- Use React Query para cache e sincronização
- Context API para estado global
- Zustand para estado complexo
- Form handling com React Hook Form

ESTILO:
- Design system consistente
- Dark/Light theme
- Animações suaves
- Componentes acessíveis

Estrutura: frontend/src/[pages|components|lib|types|hooks]/
```

### 📝 Prompt: Gerar Dashboard e Analytics

```
Crie dashboards interativos com métricas e analytics para diferentes tipos de usuários.

DASHBOARD DO RECRUITER:
- Métricas de vagas ativas
- Total de candidaturas recebidas
- Taxa de conversão
- Tempo médio de preenchimento
- Gráfico de candidaturas por período
- Top skills mais demandadas
- Ranking das melhores análises

DASHBOARD DA EMPRESA:
- Overview de todas as vagas
- Performance dos recrutadores
- Métricas de contratação
- Custo por contratação
- Diversity & Inclusion metrics
- ROI do sistema

DASHBOARD DO CANDIDATO:
- Status das candidaturas
- Feedback das análises
- Sugestões de melhoria
- Vagas recomendadas
- Progress do perfil

COMPONENTES DE ANALYTICS:

Charts (usando Recharts ou Chart.js):
- LineChart - Tendências temporais
- BarChart - Comparações
- PieChart - Distribuições
- AreaChart - Volumes
- ScatterPlot - Correlações

KPI Cards:
- Métricas em tempo real
- Comparação com período anterior
- Indicadores de tendência
- Alertas e thresholds

Filters:
- Filtro por período
- Filtro por departamento
- Filtro por tipo de vaga
- Filtro por status

Tables:
- Tabelas com sorting
- Export para CSV/PDF
- Drill-down capabilities

FEATURES AVANÇADAS:
- Real-time updates
- Export de relatórios
- Bookmarks de filtros
- Alertas personalizados
- Comparação de períodos

Use bibliotecas: Recharts, date-fns, lucide-react
Estrutura: frontend/src/components/analytics/
```

## 🐛 6. TESTES E QUALIDADE

### 📝 Prompt: Gerar Testes Automatizados

```
Crie uma suíte completa de testes para o sistema.

TESTES BACKEND (pytest):

Unit Tests:
- Testes para todos os repositories
- Testes para todos os services
- Testes para models e schemas
- Testes para utilities e helpers

Integration Tests:
- Testes de endpoints da API
- Testes de integração com banco
- Testes de integração com LLM APIs
- Testes de workflows LangGraph

E2E Tests:
- Fluxo completo de candidatura
- Fluxo de análise de currículo
- Fluxo de criação de vaga

Fixtures:
- Usuários de teste
- Empresas de teste
- Vagas de teste
- Dados de análise mock

TESTES FRONTEND (Jest + Testing Library):

Component Tests:
- Testes para todos os componentes
- Testes de interação
- Testes de formulários
- Testes de estados

Integration Tests:
- Testes de páginas completas
- Testes de fluxos de usuário
- Testes de API calls

E2E Tests (Playwright):
- Fluxo de login/logout
- Fluxo de candidatura completa
- Fluxo de criação de vaga
- Fluxo de análise

ESTRUTURA DE TESTES:

```
tests/
├── backend/
│   ├── unit/
│   │   ├── test_repositories.py
│   │   ├── test_services.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_llm_integration.py
│   │   └── test_workflows.py
│   ├── e2e/
│   │   └── test_complete_flows.py
│   └── fixtures/
│       └── test_data.py
├── frontend/
│   ├── __tests__/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── e2e/
│       └── flows.spec.ts
```

CONFIGURAÇÕES:
- Coverage mínimo de 80%
- Testes em pipeline CI/CD
- Relatórios de cobertura
- Testes de performance
- Testes de segurança

MOCKS E STUBS:
- Mock para LLM APIs
- Mock para upload de arquivos
- Stub para notificações
- Test database isolado
```

## 🚀 7. DEPLOY E INFRAESTRUTURA

### 📝 Prompt: Gerar Configuração de Deploy

```
Crie configurações completas para deploy em produção.

DOCKER:

Dockerfile backend:
- Multi-stage build
- Python slim image
- Dependências otimizadas
- Security hardening
- Health checks

Dockerfile frontend:
- Node.js para build
- Nginx para servir
- Otimização de bundle
- Compressão gzip

docker-compose.yml produção:
- Serviços: api, frontend, postgres, redis, rabbitmq
- Networks isoladas
- Volumes persistentes
- Environment variables
- Health checks
- Restart policies

KUBERNETES:

Manifests:
- Deployments para cada serviço
- Services para exposição
- ConfigMaps para configurações
- Secrets para credenciais
- Ingress para routing
- PersistentVolumes para dados

Helm Charts:
- Chart para toda a aplicação
- Values files por ambiente
- Templates parametrizados

CI/CD PIPELINE (GitHub Actions):

```yaml
name: Deploy

stages:
  - test
  - build
  - security-scan
  - deploy-staging
  - deploy-production

jobs:
  test:
    - Run unit tests
    - Run integration tests
    - Generate coverage report
  
  build:
    - Build Docker images
    - Push to registry
    - Tag with version
  
  security:
    - Vulnerability scan
    - Dependency audit
    - SAST analysis
  
  deploy:
    - Deploy to staging
    - Run E2E tests
    - Deploy to production
```

MONITORING E OBSERVABILITY:

Logging:
- Structured logging
- Centralized logs (ELK stack)
- Log rotation
- Error alerting

Metrics:
- Prometheus + Grafana
- Custom business metrics
- Infrastructure metrics
- Application performance

Tracing:
- Distributed tracing
- Request correlation
- Performance bottlenecks

Health Checks:
- Liveness probes
- Readiness probes
- Dependency checks

BACKUP E RECOVERY:
- Database backups automáticos
- File storage backup
- Disaster recovery plan
- RTO/RPO definitions

SEGURANÇA:
- TLS/SSL certificates
- WAF protection
- Rate limiting
- DDoS protection
- Secrets management
```

## 📚 8. DOCUMENTAÇÃO E MANUAIS

### 📝 Prompt: Gerar Documentação Completa

```
Crie documentação técnica e de usuário completa.

DOCUMENTAÇÃO TÉCNICA:

API Documentation:
- OpenAPI/Swagger specs completa
- Exemplos de request/response
- Códigos de erro
- Rate limits
- Authentication flows

Architecture Documentation:
- Diagramas de arquitetura
- Fluxos de dados
- Decisões técnicas
- Padrões utilizados

Database Documentation:
- Schema documentation
- Relacionamentos
- Índices e performance
- Migrations guide

LLM Integration Guide:
- Configuração de providers
- Prompt engineering
- Cost optimization
- Error handling

MANUAIS DE USUÁRIO:

Manual do Candidato:
- Como criar perfil
- Como se candidatar
- Como interpretar análises
- FAQ

Manual do Recruiter:
- Como criar vagas
- Como interpretar rankings
- Como gerar relatórios
- Best practices

Manual do Admin:
- Configuração do sistema
- Gerenciamento de usuários
- Monitoramento
- Troubleshooting

RUNBOOKS:

Deployment Runbook:
- Procedimentos de deploy
- Rollback procedures
- Environment setup
- Configuration management

Operations Runbook:
- Monitoring procedures
- Incident response
- Backup/restore
- Scaling procedures

TEMPLATES:
- README.md completo
- Contributing guidelines
- Issue templates
- PR templates
- Code of conduct

DIAGRAMAS:
- Arquitetura do sistema
- Fluxos de processo
- Database ERD
- Network topology
- Sequence diagrams

Use ferramentas: Mermaid, PlantUML, Docusaurus
```

---

## 🎯 ORDEM DE EXECUÇÃO RECOMENDADA

1. **Modelos e Schemas** (Prompts 1-2)
2. **Repositórios** (Prompt 3)
3. **Serviços** (Prompts 4-5)
4. **APIs** (Prompts 6-7)
5. **Frontend** (Prompts 8-9)
6. **Testes** (Prompt 10)
7. **Deploy** (Prompt 11)
8. **Documentação** (Prompt 12)

## 💡 DICAS DE USO

- Execute um prompt por vez
- Revise o código gerado antes de prosseguir
- Ajuste os prompts conforme necessário
- Mantenha consistência entre os componentes
- Teste cada camada antes de avançar

---

**Versão dos Prompts:** 1.0  
**Compatível com:** Claude 4, GPT-4, Gemini Pro  
**Última Atualização:** Janeiro 2025