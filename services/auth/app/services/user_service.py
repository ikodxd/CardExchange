from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.security import hash_password, verify_password
from app.settings import settings


@dataclass
class UserService:
    db: Session

    def register_user(self, email: str, username: str, password: str) -> User:
        existing = self.db.scalar(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=UserRole.user,
            balance=Decimal(str(settings.starting_balance)),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    def ensure_admin_account(self) -> None:
        if not settings.admin_email:
            return
        admin = self.db.scalar(select(User).where(User.email == settings.admin_email))
        if admin is None:
            self.db.add(User(
                email=settings.admin_email,
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role=UserRole.admin,
            ))
            self.db.commit()
            return
        needs = False
        if not verify_password(settings.admin_password, admin.password_hash):
            admin.password_hash = hash_password(settings.admin_password)
            needs = True
        if admin.role != UserRole.admin:
            admin.role = UserRole.admin
            needs = True
        if admin.username != settings.admin_username:
            admin.username = settings.admin_username
            needs = True
        if needs:
            self.db.commit()
