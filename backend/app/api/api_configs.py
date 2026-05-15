from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import httpx

from app.api.deps import get_current_user
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.api_config import (
    APIConfigCreate,
    APIConfigResponse,
    APIConfigTest,
    APIConfigTestResult,
    APIConfigUpdate,
)
from app.services.auth import APIConfigService
from app.services.llm_service import LLMService

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
            detail="未设置默认 API 配置",
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
        db,
        UUID(config_id),
        current_user.id,
        config_data,
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
    del current_user

    provider = str(test_data.provider or "").lower()
    base_url = test_data.base_url or settings.LLM_PROVIDER_URLS.get(provider)
    if not base_url:
        return APIConfigTestResult(
            success=False,
            message=f"不支持的提供商: {test_data.provider}",
        )

    if provider not in {"dashscope", "openai", "claude"}:
        return APIConfigTestResult(
            success=False,
            message=f"暂不支持 {test_data.provider} 的真实推理测试",
        )

    resolved_model = test_data.model_version or test_data.model_name
    if provider == "dashscope" and not resolved_model:
        return APIConfigTestResult(
            success=False,
            message="请提供 model_version，或在 model_name 中填写实际可调用的模型标识",
        )

    llm = LLMService(
        {
            "provider": provider,
            "api_key": test_data.api_key,
            "base_url": base_url,
            "model_version": resolved_model,
        }
    )

    try:
        await llm.generate("请只回复：OK")
    except httpx.TimeoutException:
        return APIConfigTestResult(success=False, message="最小推理调用超时，请检查网络或模型服务")
    except Exception as exc:
        return APIConfigTestResult(success=False, message=f"最小推理调用失败: {exc}")

    if test_data.model_version:
        return APIConfigTestResult(
            success=True,
            message=f"最小推理调用成功，模型: {test_data.model_version}",
        )
    if test_data.model_name:
        return APIConfigTestResult(
            success=True,
            message=f"最小推理调用成功，已使用 model_name 作为模型标识: {test_data.model_name}",
        )
    return APIConfigTestResult(success=True, message="最小推理调用成功")
