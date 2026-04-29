from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import CardRarity


class CardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
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
    is_locked: bool
    is_for_sale: bool
    sale_price: Decimal | None
    owner_id: int
    created_at: datetime


class ListForSaleRequest(BaseModel):
    sale_price: Decimal = Field(gt=0)
