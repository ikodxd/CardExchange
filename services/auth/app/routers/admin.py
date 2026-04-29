from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_role
from app.models import User, UserRole
from app.schemas import AssignRoleRequest, UserRead

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/assign-role", response_model=UserRead)
def assign_role(
    payload: AssignRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
) -> User:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admin role cannot be reassigned")
    user.role = UserRole.moderator
    db.commit()
    db.refresh(user)
    return user
