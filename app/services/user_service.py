from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.security import hash_password, verify_password
from app.settings import settings


@dataclass
class UserService:
    db: Session

    def register_user(self, email: str, username: str, password: str) -> User:
        existing_user = self.db.scalar(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=UserRole.user,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user

    def assign_moderator_role(self, email: str) -> User:
        user = self.db.scalar(select(User).where(User.email == email))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.role == UserRole.admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin role cannot be reassigned")

        user.role = UserRole.moderator
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_admin_account(self) -> None:
        if not settings.admin_email or not settings.admin_username or not settings.admin_password:
            return

        admin_user = self.db.scalar(select(User).where(User.email == settings.admin_email))
        if admin_user is None:
            admin_user = User(
                email=settings.admin_email,
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role=UserRole.admin,
            )
            self.db.add(admin_user)
            self.db.commit()
            return

        needs_update = False
        if not verify_password(settings.admin_password, admin_user.password_hash):
            admin_user.password_hash = hash_password(settings.admin_password)
            needs_update = True
        if admin_user.role != UserRole.admin:
            admin_user.role = UserRole.admin
            needs_update = True
        if admin_user.username != settings.admin_username:
            admin_user.username = settings.admin_username
            needs_update = True

        if needs_update:
            self.db.commit()
