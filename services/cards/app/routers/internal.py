from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_internal
from app.models import Card
from app.schemas import CardRead

router = APIRouter(prefix="/internal/cards", tags=["internal"], dependencies=[Depends(require_internal)])


class OwnerUpdate(BaseModel):
    new_owner_id: int


class LockUpdate(BaseModel):
    locked: bool


class DelistUpdate(BaseModel):
    pass


@router.get("/{card_id}", response_model=CardRead)
def get_card(card_id: int, db: Session = Depends(get_db)) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.patch("/{card_id}/owner", response_model=CardRead)
def transfer_owner(card_id: int, payload: OwnerUpdate, db: Session = Depends(get_db)) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.owner_id = payload.new_owner_id
    card.is_locked = False
    card.is_for_sale = False
    card.sale_price = None
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}/lock", response_model=CardRead)
def set_lock(card_id: int, payload: LockUpdate, db: Session = Depends(get_db)) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.is_locked = payload.locked
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}/delist", response_model=CardRead)
def delist_card(card_id: int, db: Session = Depends(get_db)) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.is_for_sale = False
    card.sale_price = None
    card.is_locked = False
    db.commit()
    db.refresh(card)
    return card
