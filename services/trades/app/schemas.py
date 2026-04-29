from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import OfferStatus, TransactionType


class TradeOfferCreate(BaseModel):
    offered_card_id: int
    requested_card_id: int


class TradeOfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    requester_id: int
    responder_id: int
    offered_card_id: int
    requested_card_id: int
    status: OfferStatus
    offered_card_snapshot: str
    requested_card_snapshot: str
    requester_username: str
    responder_username: str
    created_at: datetime
    updated_at: datetime


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: TransactionType
    initiator_id: int
    counterparty_id: int | None
    card_id: int
    card_name: str
    card_image_url: str
    price: Decimal
    initiator_username: str
    counterparty_username: str
    created_at: datetime


class BuyCardRequest(BaseModel):
    pass
