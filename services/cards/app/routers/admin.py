from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models import Card
from app.schemas import CardRead

router = APIRouter(prefix="/api/admin/cards", tags=["admin-cards"])


def _require_mod(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator or admin required")
    return user


@router.get("", response_model=list[CardRead])
def list_all_cards(
    is_fake: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(_require_mod),
) -> list[Card]:
    q = select(Card)
    if is_fake is not None:
        q = q.where(Card.is_fake.is_(is_fake))
    return list(db.scalars(q.offset(skip).limit(limit)).all())


@router.patch("/{card_id}/fake", response_model=CardRead)
def toggle_fake(
    card_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(_require_mod),
) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.is_fake = not card.is_fake
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", response_model=CardRead)
def delete_fake(
    card_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(_require_mod),
) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not card.is_fake:
        raise HTTPException(status_code=400, detail="Only fake cards can be deleted")
    db.delete(card)
    db.commit()
    return card
