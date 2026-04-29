from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.security import decode_access_token

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
