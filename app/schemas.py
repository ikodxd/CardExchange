from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CardRarity, TradeStatus, UserRole


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    role: UserRole


class AssignModeratorRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    role: Literal["moderator"] = "moderator"


class CardCreate(BaseModel):
    name: str
    description: str = ""
    image_url: str = ""
    rarity: CardRarity
    price: Decimal = Field(ge=0)
    power: int = Field(default=0, ge=0)
    defense: int = Field(default=0, ge=0)


class CardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    image_url: str
    rarity: CardRarity
    price: Decimal
    power: int
    defense: int
    is_fake: bool
    owner_id: int
    created_at: datetime


class TradeCreate(BaseModel):
    offered_card_id: int
    requested_card_id: int


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    responder_id: int
    offered_card_id: int
    requested_card_id: int
    status: TradeStatus
    created_at: datetime
    completed_at: datetime
