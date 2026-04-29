from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.client import delist_card, get_card, get_user, transfer_card_owner, update_balance
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models import Transaction, TransactionType
from app.publisher import publish
from app.schemas import TransactionRead

router = APIRouter(prefix="/trades", tags=["transactions"])


@router.post("/buy/{card_id}", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def buy_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Transaction:
    card = await get_card(card_id)

    if card["owner_id"] == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this card")
    if not card["is_for_sale"]:
        raise HTTPException(status_code=400, detail="Card is not listed for sale")
    if card["is_fake"]:
        raise HTTPException(status_code=400, detail="Fake cards cannot be purchased")
    if card["is_locked"]:
        raise HTTPException(status_code=400, detail="Card is locked in a pending trade")

    sale_price = Decimal(str(card["sale_price"]))
    seller_id = card["owner_id"]

    buyer = await get_user(current_user.id)
    if Decimal(str(buyer["balance"])) < sale_price:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    seller = await get_user(seller_id)

    await update_balance(current_user.id, -float(sale_price))
    await update_balance(seller_id, float(sale_price))
    await transfer_card_owner(card_id, current_user.id)
    await delist_card(card_id)

    tx = Transaction(
        type=TransactionType.buy,
        initiator_id=current_user.id,
        counterparty_id=seller_id,
        card_id=card_id,
        card_name=card["name"],
        card_image_url=card["image_url"],
        price=sale_price,
        initiator_username=current_user.username,
        counterparty_username=seller["username"],
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    await publish(f"user:{seller_id}", {
        "type": "card_sold",
        "card_name": card["name"],
        "price": float(sale_price),
        "buyer": current_user.username,
    })
    await publish(f"user:{current_user.id}", {
        "type": "card_purchased",
        "card_name": card["name"],
        "price": float(sale_price),
        "seller": seller["username"],
    })

    return tx


@router.get("/history/me", response_model=list[TransactionRead])
def get_my_history(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
) -> list[Transaction]:
    return list(db.scalars(
        select(Transaction).where(
            or_(Transaction.initiator_id == current_user.id, Transaction.counterparty_id == current_user.id)
        ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    ).all())


@router.get("/history/user/{user_id}", response_model=list[TransactionRead])
def get_user_history(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> list[Transaction]:
    return list(db.scalars(
        select(Transaction).where(
            or_(Transaction.initiator_id == user_id, Transaction.counterparty_id == user_id)
        ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    ).all())
