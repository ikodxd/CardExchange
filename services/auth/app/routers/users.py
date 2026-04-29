from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas import UserPublicRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[UserPublicRead])
def search_users(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[User]:
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    results = db.scalars(
        select(User)
        .where(User.username.ilike(f"%{q}%"))
        .where(User.is_active.is_(True))
        .limit(limit)
    ).all()
    return list(results)


@router.get("/{username}", response_model=UserPublicRead)
def get_user_profile(username: str, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
