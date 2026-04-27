from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class CardRarity(str, Enum):
    common = "common"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"


class TradeStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.user, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cards: Mapped[list["Card"]] = relationship("Card", back_populates="owner")
    requested_trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="requester",
        foreign_keys="Trade.requester_id",
    )
    received_trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="responder",
        foreign_keys="Trade.responder_id",
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    rarity: Mapped[CardRarity] = mapped_column(SqlEnum(CardRarity), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    power: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_fake: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="cards")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    responder_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    offered_card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    requested_card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    status: Mapped[TradeStatus] = mapped_column(SqlEnum(TradeStatus), default=TradeStatus.completed, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    requester: Mapped["User"] = relationship("User", back_populates="requested_trades", foreign_keys=[requester_id])
    responder: Mapped["User"] = relationship("User", back_populates="received_trades", foreign_keys=[responder_id])
