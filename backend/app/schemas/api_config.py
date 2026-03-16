from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class APIConfigBase(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = Field(None, max_length=500)
    model_version: Optional[str] = Field(None, max_length=100)
    is_default: bool = False


class APIConfigCreate(APIConfigBase):
    pass


class APIConfigUpdate(BaseModel):
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    api_key: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = Field(None, max_length=500)
    model_version: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None


class APIConfigResponse(BaseModel):
    id: UUID
    model_name: str
    provider: str
    api_key_masked: str
    base_url: Optional[str]
    model_version: Optional[str]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIConfigTest(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model_version: Optional[str] = None


class APIConfigTestResult(BaseModel):
    success: bool
    message: str
