from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.email import send_reset_email
from app.limiter import limiter
from app.models import User
from app.schemas import (
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest,
    TokenResponse, UserCreate, UserLogin, UserRead,
)
from app.security import create_access_token, generate_reset_token, hash_password, verify_password
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

AVATAR_DIR = Path("data/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    return UserService(db).register_user(payload.email, payload.username, payload.password)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = UserService(db).authenticate_user(payload.username, payload.password)
    token = create_access_token({"id": user.id, "role": user.role.value, "username": user.username})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if user:
        token = generate_reset_token()
        user.reset_token = token
        user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
        db.commit()
        await send_reset_email(user.email, token)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.reset_token == payload.token))
    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    user.password_hash = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Password reset successfully"}


@router.put("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    filename = f"avatar_{current_user.id}{ext}"
    dest = AVATAR_DIR / filename
    dest.write_bytes(await file.read())
    current_user.avatar_url = f"/auth/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user
