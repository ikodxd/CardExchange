from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models import Card, CardRarity
from app.schemas import CardCreate, CardRead, ListForSaleRequest

router = APIRouter(prefix="/cards", tags=["cards"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Card:
    if current_user.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator or admin required")
    card = Card(**payload.model_dump(), owner_id=current_user.id)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    if current_user.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator or admin required")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    import secrets as _s
    filename = f"{_s.token_hex(12)}{ext}"
    (UPLOAD_DIR / filename).write_bytes(await file.read())
    return {"url": f"/cards/uploads/{filename}"}


@router.get("", response_model=list[CardRead])
def list_cards(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    rarity: CardRarity | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    for_sale: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Card]:
    q = select(Card).where(Card.is_fake.is_(False))
    if search:
        q = q.where(Card.name.ilike(f"%{search}%"))
    if rarity is not None:
        q = q.where(Card.rarity == rarity)
    if min_price is not None:
        q = q.where(Card.price >= min_price)
    if max_price is not None:
        q = q.where(Card.price <= max_price)
    if for_sale is True:
        q = q.where(Card.is_for_sale.is_(True))
    elif for_sale is False:
        q = q.where(Card.is_for_sale.is_(False))
    q = q.offset(skip).limit(limit).order_by(Card.created_at.desc())
    return list(db.scalars(q).all())


@router.get("/user/{user_id}", response_model=list[CardRead])
def get_user_cards(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Card]:
    return list(db.scalars(
        select(Card)
        .where(Card.owner_id == user_id)
        .where(Card.is_fake.is_(False))
        .offset(skip).limit(limit)
        .order_by(Card.created_at.desc())
    ).all())


@router.get("/{card_id}", response_model=CardRead)
def get_card(card_id: int, db: Session = Depends(get_db)) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.post("/{card_id}/list", response_model=CardRead)
def list_for_sale(
    card_id: int,
    payload: ListForSaleRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this card")
    if card.is_locked:
        raise HTTPException(status_code=400, detail="Card is locked in a pending trade")
    if card.is_fake:
        raise HTTPException(status_code=400, detail="Fake cards cannot be listed")
    card.is_for_sale = True
    card.sale_price = payload.sale_price
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}/list", response_model=CardRead)
def delist_from_sale(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this card")
    card.is_for_sale = False
    card.sale_price = None
    db.commit()
    db.refresh(card)
    return card
