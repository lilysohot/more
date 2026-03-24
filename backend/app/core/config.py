from pydantic_settings import BaseSettings
from typing import List, Dict
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "公司分析研报助手"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = ""  # 必须从环境变量设置
    DATABASE_URL_FALLBACK: str = "postgresql://analyst:password@localhost:5432/analyst_db"  # 仅用于本地开发
    
    REDIS_URL: str = "redis://localhost:6379"
    
    SECRET_KEY: str = ""  # 必须从环境变量设置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    REMEMBER_ME_EXPIRE_DAYS: int = 30
    
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    ENCRYPTION_KEY: str = ""  # 必须从环境变量设置
    
    MAX_API_CONFIGS_PER_USER: int = 10
    
    DEBUG: bool = False
    
    DEFAULT_LLM_PROVIDER: str = "dashscope"
    DEFAULT_LLM_MODEL: str = "qwen3.5-plus"
    DEFAULT_LLM_API_KEY: str = ""  # 必须从环境变量设置
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # LLM Provider 默认 Base URLs
    LLM_PROVIDER_URLS: Dict[str, str] = {
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
        "claude": "https://api.anthropic.com/v1",
    }
    
    def _validate_required_secrets(self):
        """
        验证必需的安全配置是否已设置
        在生产环境中，如果检测到使用默认值，将拒绝启动
        """
        warnings = []
        errors = []
        
        # 检查 SECRET_KEY
        if not self.SECRET_KEY:
            errors.append("SECRET_KEY 未设置，请设置环境变量 SECRET_KEY")
        elif self.SECRET_KEY in ["your-secret-key-change-in-production", "dev-secret-key"]:
            if self.DEBUG:
                warnings.append("SECRET_KEY 使用了不安全默认值，生产环境请更换")
            else:
                errors.append("SECRET_KEY 使用了不安全默认值，生产环境必须更换")
        
        # 检查 ENCRYPTION_KEY
        if not self.ENCRYPTION_KEY:
            errors.append("ENCRYPTION_KEY 未设置，请设置环境变量 ENCRYPTION_KEY")
        elif self.ENCRYPTION_KEY in ["your-32-byte-encryption-key-here!!!", "dev-encryption-key-32-bytes-long!!"]:
            if self.DEBUG:
                warnings.append("ENCRYPTION_KEY 使用了不安全默认值，生产环境请更换")
            else:
                errors.append("ENCRYPTION_KEY 使用了不安全默认值，生产环境必须更换")
        
        # 检查 DATABASE_URL
        if not self.DATABASE_URL:
            if self.DEBUG:
                warnings.append("DATABASE_URL 未设置，使用本地开发默认值")
            else:
                errors.append("DATABASE_URL 未设置，请设置环境变量 DATABASE_URL")
        
        # 检查 DEFAULT_LLM_API_KEY（可选，但建议设置）
        if not self.DEFAULT_LLM_API_KEY:
            warnings.append("DEFAULT_LLM_API_KEY 未设置，用户需要配置自己的 API Key")
        
        # 输出警告
        for w in warnings:
            logger.warning(w)
        
        # 输出错误并拒绝启动（非DEBUG模式）
        if errors:
            for e in errors:
                logger.error(e)
            if not self.DEBUG:
                raise ValueError(f"配置验证失败: {', '.join(errors)}")
    
    @property
    def database_url_effective(self) -> str:
        """获取实际使用的数据库URL"""
        return self.DATABASE_URL or self.DATABASE_URL_FALLBACK if self.DEBUG else self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # 启动时验证配置
    settings._validate_required_secrets()
    return settings


settings = get_settings()
