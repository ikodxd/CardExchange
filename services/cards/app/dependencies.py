from fastapi import Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.security import decode_access_token
from app.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CurrentUser:
    def __init__(self, id: int, role: str, username: str):
        self.id = id
        self.role = role
        self.username = username


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    payload = decode_access_token(token)
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return CurrentUser(id=user_id, role=payload.get("role", "user"), username=payload.get("username", ""))


def require_mod_or_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator or admin required")
    return user


def require_internal(x_internal_key: str = Header(default="")):
    if x_internal_key != settings.internal_secret:
        raise HTTPException(status_code=403, detail="Invalid internal key")
