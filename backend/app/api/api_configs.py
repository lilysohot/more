from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import httpx
from app.database import get_db
from app.models.user import User
from app.schemas.api_config import (
    APIConfigCreate, APIConfigUpdate, APIConfigResponse,
    APIConfigTest, APIConfigTestResult
)
from app.services.auth import APIConfigService
from app.api.deps import get_current_user

router = APIRouter()


def config_to_response(config) -> APIConfigResponse:
    return APIConfigResponse(
        id=config.id,
        model_name=config.model_name,
        provider=config.provider,
        api_key_masked=APIConfigService.mask_config_key(config),
        base_url=config.base_url,
        model_version=config.model_version,
        is_default=config.is_default,
        created_at=config.created_at,
    )


@router.get("", response_model=List[APIConfigResponse])
async def get_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    configs = await APIConfigService.get_user_configs(db, current_user.id)
    return [config_to_response(c) for c in configs]


@router.post("", response_model=APIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: APIConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await APIConfigService.create_config(db, current_user.id, config_data)
    return config_to_response(config)


@router.get("/default", response_model=APIConfigResponse)
async def get_default_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await APIConfigService.get_default_config(db, current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未设置默认 API 配置"
        )
    return config_to_response(config)


@router.put("/{config_id}", response_model=APIConfigResponse)
async def update_config(
    config_id: str,
    config_data: APIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    config = await APIConfigService.update_config(
        db, UUID(config_id), current_user.id, config_data
    )
    return config_to_response(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    await APIConfigService.delete_config(db, UUID(config_id), current_user.id)


@router.post("/{config_id}/set-default", response_model=APIConfigResponse)
async def set_default_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    config = await APIConfigService.set_default(db, UUID(config_id), current_user.id)
    return config_to_response(config)


@router.post("/test", response_model=APIConfigTestResult)
async def test_config(
    test_data: APIConfigTest,
    current_user: User = Depends(get_current_user),
):
    try:
        base_url = test_data.base_url
        if not base_url:
            provider_urls = {
                "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "openai": "https://api.openai.com/v1",
                "claude": "https://api.anthropic.com/v1",
            }
            base_url = provider_urls.get(test_data.provider.lower())
        
        if not base_url:
            return APIConfigTestResult(
                success=False,
                message=f"不支持的提供商: {test_data.provider}"
            )
        
        if test_data.provider.lower() in ["openai", "dashscope"]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {test_data.api_key}"},
                )
                if response.status_code == 200:
                    return APIConfigTestResult(success=True, message="连接成功")
                else:
                    return APIConfigTestResult(
                        success=False,
                        message=f"连接失败: HTTP {response.status_code}"
                    )
        elif test_data.provider.lower() == "claude":
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={
                        "x-api-key": test_data.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                if response.status_code == 200:
                    return APIConfigTestResult(success=True, message="连接成功")
                else:
                    return APIConfigTestResult(
                        success=False,
                        message=f"连接失败: HTTP {response.status_code}"
                    )
        else:
            return APIConfigTestResult(
                success=True,
                message="配置已保存，请在实际使用时验证"
            )
    except httpx.TimeoutException:
        return APIConfigTestResult(success=False, message="连接超时，请检查网络")
    except Exception as e:
        return APIConfigTestResult(success=False, message=f"连接失败: {str(e)}")
