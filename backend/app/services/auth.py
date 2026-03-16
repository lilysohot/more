from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user import User, APIConfig, Analysis
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.api_config import APIConfigCreate, APIConfigUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import (
    UserAlreadyExistsException, InvalidPasswordException, UserNotFoundException,
    APIConfigLimitException, APIConfigNotFoundException
)
from app.utils.encryption import encrypt_api_key, decrypt_api_key, mask_api_key
from app.core.config import settings
from uuid import UUID


class AuthService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        existing_user = await AuthService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise UserAlreadyExistsException("该邮箱已被注册")
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        user = await AuthService.get_user_by_email(db, email)
        if not user:
            raise InvalidPasswordException("邮箱或密码错误")
        
        if not verify_password(password, user.password_hash):
            raise InvalidPasswordException("邮箱或密码错误")
        
        if not user.is_active:
            raise InvalidPasswordException("用户已被禁用")
        
        return user
    
    @staticmethod
    async def update_user(db: AsyncSession, user: User, user_data: UserUpdate) -> User:
        if user_data.username is not None:
            user.username = user_data.username
        await db.commit()
        await db.refresh(user)
        return user


class APIConfigService:
    @staticmethod
    async def get_user_configs(db: AsyncSession, user_id: UUID) -> list[APIConfig]:
        result = await db.execute(
            select(APIConfig).where(APIConfig.user_id == user_id).order_by(APIConfig.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_config_by_id(db: AsyncSession, config_id: UUID, user_id: UUID) -> Optional[APIConfig]:
        result = await db.execute(
            select(APIConfig).where(APIConfig.id == config_id, APIConfig.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_default_config(db: AsyncSession, user_id: UUID) -> Optional[APIConfig]:
        result = await db.execute(
            select(APIConfig).where(APIConfig.user_id == user_id, APIConfig.is_default == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_config(db: AsyncSession, user_id: UUID, config_data: APIConfigCreate) -> APIConfig:
        existing_configs = await APIConfigService.get_user_configs(db, user_id)
        if len(existing_configs) >= settings.MAX_API_CONFIGS_PER_USER:
            raise APIConfigLimitException()
        
        if config_data.is_default:
            await APIConfigService._unset_default(db, user_id)
        
        config = APIConfig(
            user_id=user_id,
            model_name=config_data.model_name,
            provider=config_data.provider,
            api_key_encrypted=encrypt_api_key(config_data.api_key),
            base_url=config_data.base_url,
            model_version=config_data.model_version,
            is_default=config_data.is_default,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def update_config(
        db: AsyncSession, config_id: UUID, user_id: UUID, config_data: APIConfigUpdate
    ) -> APIConfig:
        config = await APIConfigService.get_config_by_id(db, config_id, user_id)
        if not config:
            raise APIConfigNotFoundException()
        
        if config_data.model_name is not None:
            config.model_name = config_data.model_name
        if config_data.provider is not None:
            config.provider = config_data.provider
        if config_data.api_key is not None:
            config.api_key_encrypted = encrypt_api_key(config_data.api_key)
        if config_data.base_url is not None:
            config.base_url = config_data.base_url
        if config_data.model_version is not None:
            config.model_version = config_data.model_version
        if config_data.is_default is not None:
            if config_data.is_default:
                await APIConfigService._unset_default(db, user_id)
            config.is_default = config_data.is_default
        
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def delete_config(db: AsyncSession, config_id: UUID, user_id: UUID) -> bool:
        config = await APIConfigService.get_config_by_id(db, config_id, user_id)
        if not config:
            raise APIConfigNotFoundException()
        
        await db.delete(config)
        await db.commit()
        return True
    
    @staticmethod
    async def set_default(db: AsyncSession, config_id: UUID, user_id: UUID) -> APIConfig:
        config = await APIConfigService.get_config_by_id(db, config_id, user_id)
        if not config:
            raise APIConfigNotFoundException()
        
        await APIConfigService._unset_default(db, user_id)
        config.is_default = True
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def _unset_default(db: AsyncSession, user_id: UUID):
        result = await db.execute(
            select(APIConfig).where(APIConfig.user_id == user_id, APIConfig.is_default == True)
        )
        configs = result.scalars().all()
        for config in configs:
            config.is_default = False
        await db.commit()
    
    @staticmethod
    def mask_config_key(config: APIConfig) -> str:
        api_key = decrypt_api_key(config.api_key_encrypted)
        return mask_api_key(api_key)


class AnalysisService:
    @staticmethod
    async def get_user_analyses(
        db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Analysis]:
        result = await db.execute(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def count_user_analyses(db: AsyncSession, user_id: UUID) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.user_id == user_id)
        )
        return result.scalar()
