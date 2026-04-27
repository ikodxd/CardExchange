from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.security import decode_access_token
from app.services.user_service import UserService
from app.settings import settings


def build_test_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    object.__setattr__(settings, "admin_email", "admin@example.com")
    object.__setattr__(settings, "admin_username", "root_admin")
    object.__setattr__(settings, "admin_password", "admin-secret")
    return TestClient(app), testing_session_local


def test_register_always_creates_regular_user(monkeypatch):
    client, session_local = build_test_client(monkeypatch)

    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "regular_user",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "user"

    with session_local() as db:
        user = db.scalar(select(User).where(User.email == "user@example.com"))
        assert user is not None
        assert user.role == UserRole.user


def test_register_rejects_role_field_from_client(monkeypatch):
    client, _ = build_test_client(monkeypatch)

    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "regular_user",
            "password": "secret123",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_login_token_contains_id_and_role(monkeypatch):
    client, _ = build_test_client(monkeypatch)

    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "regular_user",
            "password": "secret123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "regular_user",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    payload = decode_access_token(response.json()["access_token"])
    assert payload["role"] == "user"
    assert isinstance(payload["id"], int)


def test_assign_role_requires_admin(monkeypatch):
    client, _ = build_test_client(monkeypatch)

    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "regular_user",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "username": "regular_user",
            "password": "secret123",
        },
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/admin/assign-role",
        json={"email": "user@example.com", "role": "moderator"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_can_assign_moderator_role(monkeypatch):
    client, session_local = build_test_client(monkeypatch)

    with session_local() as db:
        UserService(db).ensure_admin_account()

    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "regular_user",
            "password": "secret123",
        },
    )

    admin_login = client.post(
        "/auth/login",
        json={
            "username": "root_admin",
            "password": "admin-secret",
        },
    )
    admin_token = admin_login.json()["access_token"]

    response = client.post(
        "/api/admin/assign-role",
        json={"email": "user@example.com", "role": "moderator"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "moderator"
