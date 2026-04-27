from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TradeCreate, TradeRead
from app.services.trade_service import TradeService


router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    payload: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TradeService(db)
    return service.execute_trade(
        requester=current_user,
        offered_card_id=payload.offered_card_id,
        requested_card_id=payload.requested_card_id,
    )
