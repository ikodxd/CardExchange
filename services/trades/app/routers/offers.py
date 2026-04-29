from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.client import get_card, get_user, lock_card, transfer_card_owner
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models import OfferStatus, TradeOffer, Transaction, TransactionType
from app.publisher import publish
from app.schemas import TradeOfferCreate, TradeOfferRead

router = APIRouter(prefix="/trades/offers", tags=["offers"])


def _snap(card: dict) -> str:
    return json.dumps({
        "id": card["id"],
        "name": card["name"],
        "image_url": card["image_url"],
        "rarity": card["rarity"],
        "power": card["power"],
        "defense": card["defense"],
        "price": str(card["price"]),
    })


@router.post("", response_model=TradeOfferRead, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: TradeOfferCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TradeOffer:
    if payload.offered_card_id == payload.requested_card_id:
        raise HTTPException(status_code=400, detail="Cards must be different")

    offered = await get_card(payload.offered_card_id)
    requested = await get_card(payload.requested_card_id)

    if offered["owner_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own the offered card")
    if requested["owner_id"] == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")
    if offered["is_fake"] or requested["is_fake"]:
        raise HTTPException(status_code=400, detail="Fake cards cannot be traded")
    if offered["is_locked"]:
        raise HTTPException(status_code=400, detail="Your card is locked in another pending trade")
    if requested["is_locked"]:
        raise HTTPException(status_code=400, detail="The requested card is locked in another pending trade")

    responder = await get_user(requested["owner_id"])

    await lock_card(payload.offered_card_id, True)
    await lock_card(payload.requested_card_id, True)

    offer = TradeOffer(
        requester_id=current_user.id,
        responder_id=responder["id"],
        offered_card_id=payload.offered_card_id,
        requested_card_id=payload.requested_card_id,
        offered_card_snapshot=_snap(offered),
        requested_card_snapshot=_snap(requested),
        requester_username=current_user.username,
        responder_username=responder["username"],
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    await publish(f"user:{responder['id']}", {
        "type": "trade_offer_received",
        "offer_id": offer.id,
        "from": current_user.username,
        "card_name": requested["name"],
    })

    return offer


@router.get("/mine", response_model=list[TradeOfferRead])
def get_my_offers(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[TradeOffer]:
    return list(db.scalars(
        select(TradeOffer).where(
            or_(TradeOffer.requester_id == current_user.id, TradeOffer.responder_id == current_user.id)
        ).order_by(TradeOffer.created_at.desc())
    ).all())


@router.post("/{offer_id}/accept", response_model=TradeOfferRead)
async def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TradeOffer:
    offer = db.scalar(select(TradeOffer).where(TradeOffer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.responder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the responder of this offer")
    if offer.status != OfferStatus.pending:
        raise HTTPException(status_code=400, detail="Offer is no longer pending")

    await transfer_card_owner(offer.offered_card_id, offer.responder_id)
    await transfer_card_owner(offer.requested_card_id, offer.requester_id)

    offer.status = OfferStatus.accepted
    offer.updated_at = datetime.now(UTC)

    tx = Transaction(
        type=TransactionType.trade,
        initiator_id=offer.requester_id,
        counterparty_id=offer.responder_id,
        card_id=offer.offered_card_id,
        card_name=json.loads(offer.offered_card_snapshot).get("name", ""),
        card_image_url=json.loads(offer.offered_card_snapshot).get("image_url", ""),
        price=0,
        initiator_username=offer.requester_username,
        counterparty_username=offer.responder_username,
    )
    db.add(tx)
    db.commit()
    db.refresh(offer)

    await publish(f"user:{offer.requester_id}", {
        "type": "trade_accepted",
        "offer_id": offer.id,
        "by": current_user.username,
    })

    return offer


@router.post("/{offer_id}/reject", response_model=TradeOfferRead)
async def reject_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TradeOffer:
    offer = db.scalar(select(TradeOffer).where(TradeOffer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.responder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the responder of this offer")
    if offer.status != OfferStatus.pending:
        raise HTTPException(status_code=400, detail="Offer is no longer pending")

    await lock_card(offer.offered_card_id, False)
    await lock_card(offer.requested_card_id, False)

    offer.status = OfferStatus.rejected
    offer.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(offer)

    await publish(f"user:{offer.requester_id}", {
        "type": "trade_rejected",
        "offer_id": offer.id,
        "by": current_user.username,
    })

    return offer


@router.post("/{offer_id}/cancel", response_model=TradeOfferRead)
async def cancel_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TradeOffer:
    offer = db.scalar(select(TradeOffer).where(TradeOffer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the requester of this offer")
    if offer.status != OfferStatus.pending:
        raise HTTPException(status_code=400, detail="Offer is no longer pending")

    await lock_card(offer.offered_card_id, False)
    await lock_card(offer.requested_card_id, False)

    offer.status = OfferStatus.cancelled
    offer.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(offer)

    return offer
