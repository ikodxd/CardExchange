from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_any_role, require_role
from app.models import Card, User, UserRole
from app.schemas import AssignModeratorRoleRequest, CardRead, UserRead
from app.services.user_service import UserService


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/assign-role", response_model=UserRead)
def assign_moderator_role(
    payload: AssignModeratorRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
) -> User:
    service = UserService(db)
    return service.assign_moderator_role(payload.email)


@router.delete("/cards/{card_id}", response_model=CardRead)
def delete_fake_card(
    card_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role(UserRole.moderator, UserRole.admin)),
) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id))
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    if not card.is_fake:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only fake cards can be deleted")

    db.delete(card)
    db.commit()
    return card
