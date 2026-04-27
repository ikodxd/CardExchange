from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Card, CardRarity, User
from app.schemas import CardCreate, CardRead


router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Card:
    card = Card(**payload.model_dump(), owner_id=current_user.id)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.get("", response_model=list[CardRead])
def list_cards(
    db: Session = Depends(get_db),
    rarity: CardRarity | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Card]:
    query: Select[tuple[Card]] = select(Card).where(Card.is_fake.is_(False))

    if rarity is not None:
        query = query.where(Card.rarity == rarity)
    if min_price is not None:
        query = query.where(Card.price >= min_price)
    if max_price is not None:
        query = query.where(Card.price <= max_price)

    query = query.offset(skip).limit(limit).order_by(Card.created_at.desc())
    return list(db.scalars(query).all())
