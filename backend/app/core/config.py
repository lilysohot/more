from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "公司分析研报助手"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql://moremoney:moremoney123@localhost:5433/moremoney_db"
    
    REDIS_URL: str = "redis://localhost:6379"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    REMEMBER_ME_EXPIRE_DAYS: int = 30
    
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here!!!"
    
    MAX_API_CONFIGS_PER_USER: int = 10
    
    DEBUG: bool = False
    
    DEFAULT_LLM_PROVIDER: str = "dashscope"
    DEFAULT_LLM_MODEL: str = "qwen3.5-plus"
    DEFAULT_LLM_API_KEY: str = ""
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
