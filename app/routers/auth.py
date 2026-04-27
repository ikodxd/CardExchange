from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserRead
from app.security import create_access_token
from app.services.user_service import UserService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    service = UserService(db)
    return service.register_user(
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    service = UserService(db)
    user = service.authenticate_user(payload.username, payload.password)
    return TokenResponse(
        access_token=create_access_token(
            {
                "id": user.id,
                "role": user.role.value,
                "username": user.username,
            }
        )
    )


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
