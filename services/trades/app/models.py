from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class OfferStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"
    trade = "trade"


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    responder_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    offered_card_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_card_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OfferStatus] = mapped_column(SqlEnum(OfferStatus), default=OfferStatus.pending, nullable=False)
    offered_card_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    requested_card_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    requester_username: Mapped[str] = mapped_column(String(100), default="")
    responder_username: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[TransactionType] = mapped_column(SqlEnum(TransactionType), nullable=False)
    initiator_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    counterparty_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    card_id: Mapped[int] = mapped_column(Integer, nullable=False)
    card_name: Mapped[str] = mapped_column(String(120), default="")
    card_image_url: Mapped[str] = mapped_column(String(500), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    initiator_username: Mapped[str] = mapped_column(String(100), default="")
    counterparty_username: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
