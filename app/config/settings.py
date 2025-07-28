# =============================================
# app/config/settings.py
# =============================================
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # =============================================
    # APP CONFIGURATION
    # =============================================
    APP_NAME: str = Field(default="Resume Analyzer API", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # =============================================
    # DATABASE CONFIGURATION
    # =============================================
    DATABASE_URL: str = Field(..., description="Async database URL")
    DATABASE_URL_SYNC: str = Field(..., description="Sync database URL for migrations")
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql+asyncpg://', 'postgresql://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL URL')
        return v
    
    # =============================================
    # SECURITY CONFIGURATION
    # =============================================
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    # =============================================
    # CORS CONFIGURATION
    # =============================================
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed hosts for CORS"
    )
    
    # =============================================
    # LLM API CONFIGURATION
    # =============================================
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = Field(default="openai", description="Default LLM provider")
    LLM_MAX_TOKENS: int = Field(default=4000, description="Maximum tokens for LLM requests")
    LLM_TEMPERATURE: float = Field(default=0.1, description="LLM temperature")
    LLM_TIMEOUT: int = Field(default=60, description="LLM request timeout in seconds")
    LLM_MAX_RETRIES: int = Field(default=3, description="Maximum retries for LLM requests")
    
    @validator('DEFAULT_LLM_PROVIDER')
    def validate_llm_provider(cls, v):
        valid_providers = ['openai', 'anthropic', 'groq', 'gemini']
        if v not in valid_providers:
            raise ValueError(f'DEFAULT_LLM_PROVIDER must be one of: {valid_providers}')
        return v
    
    # =============================================
    # FILE UPLOAD CONFIGURATION
    # =============================================
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["application/pdf", "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain"],
        description="Allowed MIME types for file upload"
    )
    UPLOAD_DIRECTORY: str = Field(default="uploads", description="Directory for uploaded files")
    
    # =============================================
    # RABBITMQ CONFIGURATION
    # =============================================
    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ connection URL"
    )
    
    # =============================================
    # REDIS CONFIGURATION (for caching)
    # =============================================
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching"
    )
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    
    # =============================================
    # EMAIL CONFIGURATION
    # =============================================
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    
    FROM_EMAIL: str = Field(
        default="noreply@resume-analyzer.com",
        description="Default from email address"
    )
    
    # =============================================
    # LOGGING CONFIGURATION
    # =============================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')
        return v.upper()
    
    # =============================================
    # RATE LIMITING CONFIGURATION
    # =============================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Number of requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=3600, description="Rate limit window in seconds")
    
    # =============================================
    # ANALYSIS CONFIGURATION
    # =============================================
    ANALYSIS_QUEUE_NAME: str = Field(default="analysis_queue", description="Analysis queue name")
    ANALYSIS_BATCH_SIZE: int = Field(default=10, description="Batch size for analysis processing")
    ANALYSIS_TIMEOUT: int = Field(default=300, description="Analysis timeout in seconds")
    
    # Score weights for analysis (should sum to 100%)
    SCORE_WEIGHT_EXPERIENCE: float = Field(default=0.35, description="Weight for experience score")
    SCORE_WEIGHT_ACADEMIC: float = Field(default=0.30, description="Weight for academic score")
    SCORE_WEIGHT_COURSES: float = Field(default=0.20, description="Weight for courses score")
    SCORE_WEIGHT_STRONG_POINTS: float = Field(default=0.15, description="Weight for strong points")
    SCORE_WEIGHT_WEAK_POINTS: float = Field(default=-0.10, description="Weight for weak points (negative)")
    
    @validator('SCORE_WEIGHT_EXPERIENCE', 'SCORE_WEIGHT_ACADEMIC', 'SCORE_WEIGHT_COURSES', 'SCORE_WEIGHT_STRONG_POINTS')
    def validate_positive_weights(cls, v):
        if v < 0:
            raise ValueError('Score weights must be positive (except weak points)')
        return v
    
    # =============================================
    # MONITORING CONFIGURATION
    # =============================================
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    
    # =============================================
    # ENVIRONMENT CONFIGURATION
    # =============================================
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'ENVIRONMENT must be one of: {valid_envs}')
        return v
    
    # =============================================
    # MODEL CONFIGURATION
    # =============================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Atualizado para Pydantic v2
        json_schema_extra = {
            "example": {
                "APP_NAME": "Resume Analyzer API",
                "DEBUG": False,
                "DATABASE_URL": "postgresql+asyncpg://user:password@localhost:5432/resume_analyzer",
                "SECRET_KEY": "your-super-secret-key-change-in-production",
                "OPENAI_API_KEY": "sk-...",
                "ANTHROPIC_API_KEY": "sk-ant-...",
                "ALLOWED_HOSTS": ["https://yourdomain.com"],
                "ENVIRONMENT": "production"
            }
        }
    
    # =============================================
    # COMPUTED PROPERTIES
    # =============================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"
    
    @property
    def has_llm_provider(self) -> bool:
        """Check if at least one LLM provider is configured"""
        return any([
            self.OPENAI_API_KEY,
            self.ANTHROPIC_API_KEY,
            self.GROQ_API_KEY,
            self.GEMINI_API_KEY
        ])
    
    @property
    def available_llm_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if self.GROQ_API_KEY:
            providers.append("groq")
        if self.GEMINI_API_KEY:
            providers.append("gemini")
        return providers
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with appropriate driver"""
        return self.DATABASE_URL if async_driver else self.DATABASE_URL_SYNC
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration dictionary"""
        return {
            "default_provider": self.DEFAULT_LLM_PROVIDER,
            "max_tokens": self.LLM_MAX_TOKENS,
            "temperature": self.LLM_TEMPERATURE,
            "timeout": self.LLM_TIMEOUT,
            "max_retries": self.LLM_MAX_RETRIES,
            "available_providers": self.available_llm_providers
        }
    
    def get_score_weights(self) -> dict:
        """Get analysis score weights"""
        return {
            "experience": self.SCORE_WEIGHT_EXPERIENCE,
            "academic": self.SCORE_WEIGHT_ACADEMIC,
            "courses": self.SCORE_WEIGHT_COURSES,
            "strong_points": self.SCORE_WEIGHT_STRONG_POINTS,
            "weak_points": self.SCORE_WEIGHT_WEAK_POINTS
        }

# =============================================
# SETTINGS INSTANCE
# =============================================
@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)"""
    return Settings()

# ESSA É A LINHA QUE ESTAVA FALTANDO!
# Criar instância global para importação direta
settings = get_settings()

# =============================================
# ENVIRONMENT VALIDATION
# =============================================
def validate_environment():
    """Validate environment configuration"""
    current_settings = get_settings()
    
    errors = []
    
    # Check required LLM provider
    if not current_settings.has_llm_provider:
        errors.append("At least one LLM provider API key must be configured")
    
    # Check production requirements
    if current_settings.is_production:
        if current_settings.DEBUG:
            errors.append("DEBUG must be False in production")
        
        if "localhost" in current_settings.ALLOWED_HOSTS:
            errors.append("ALLOWED_HOSTS should not include localhost in production")
        
        if len(current_settings.SECRET_KEY) < 64:
            errors.append("SECRET_KEY should be at least 64 characters in production")
    
    # Check score weights sum (approximately 100%)
    total_weight = (
        current_settings.SCORE_WEIGHT_EXPERIENCE +
        current_settings.SCORE_WEIGHT_ACADEMIC +
        current_settings.SCORE_WEIGHT_COURSES +
        current_settings.SCORE_WEIGHT_STRONG_POINTS +
        abs(current_settings.SCORE_WEIGHT_WEAK_POINTS)  # Weak points is negative
    )
    
    if not (0.95 <= total_weight <= 1.05):  # Allow 5% tolerance
        errors.append(f"Score weights should sum to approximately 1.0, got {total_weight}")
    
    if errors:
        raise ValueError(f"Environment validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    return True

# =============================================
# STARTUP VALIDATION
# =============================================
if __name__ == "__main__":
    # Validate environment when running directly
    try:
        validate_environment()
        print("✅ Environment configuration is valid")
        
        current_settings = get_settings()
        print(f"✅ App: {current_settings.APP_NAME} v{current_settings.VERSION}")
        print(f"✅ Environment: {current_settings.ENVIRONMENT}")
        print(f"✅ Debug mode: {current_settings.DEBUG}")
        print(f"✅ Available LLM providers: {current_settings.available_llm_providers}")
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        exit(1)