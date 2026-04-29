from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_internal
from app.models import User
from app.schemas import BalanceUpdateRequest, UserInternalRead

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal)])


@router.get("/users/{user_id}", response_model=UserInternalRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/balance")
def update_balance(
    user_id: int,
    payload: BalanceUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_balance = Decimal(str(user.balance)) + payload.delta
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    user.balance = new_balance
    db.commit()
    return {"id": user.id, "balance": float(user.balance)}
