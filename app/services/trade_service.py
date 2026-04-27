from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, Trade, TradeStatus, User
from app.tasks import send_trade_email_notifications


@dataclass
class TradeService:
    db: Session

    def execute_trade(self, requester: User, offered_card_id: int, requested_card_id: int) -> Trade:
        if offered_card_id == requested_card_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cards must be different")

        offered_card = self.db.scalar(select(Card).where(Card.id == offered_card_id))
        requested_card = self.db.scalar(select(Card).where(Card.id == requested_card_id))

        if not offered_card or not requested_card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more cards were not found")

        if offered_card.owner_id != requester.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requester does not own offered card")

        if requested_card.owner_id == requester.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot trade with yourself")

        if offered_card.is_fake or requested_card.is_fake:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fake cards cannot be traded")

        responder = requested_card.owner
        if responder is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested card has no owner")

        with self.db.begin_nested():
            original_offered_owner_id = offered_card.owner_id
            original_requested_owner_id = requested_card.owner_id

            offered_card.owner_id = original_requested_owner_id
            requested_card.owner_id = original_offered_owner_id

            trade = Trade(
                requester_id=requester.id,
                responder_id=responder.id,
                offered_card_id=offered_card.id,
                requested_card_id=requested_card.id,
                status=TradeStatus.completed,
                completed_at=datetime.now(UTC),
            )
            self.db.add(trade)

        self.db.commit()
        self.db.refresh(trade)

        send_trade_email_notifications.delay(requester.email, responder.email, trade.id)
        return trade
