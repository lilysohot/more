from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.analysis import AnalysisResponse
from app.services.auth import AuthService, AnalysisService
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.update_user(db, current_user, user_data)
    return UserResponse.model_validate(user)


@router.get("/history", response_model=List[AnalysisResponse])
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    analyses = await AnalysisService.get_user_analyses(db, current_user.id, skip, limit)
    return [AnalysisResponse.model_validate(a) for a in analyses]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_analyses = await AnalysisService.count_user_analyses(db, current_user.id)
    return {
        "total_analyses": total_analyses,
        "member_since": current_user.created_at.isoformat(),
    }
