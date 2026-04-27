import pytest
from fastapi import HTTPException

from app.models import Card, CardRarity, TradeStatus, User
from app.security import hash_password
from app.services.trade_service import TradeService


def create_user(username: str, email: str) -> User:
    return User(username=username, email=email, password_hash=hash_password("secret123"))


def create_card(owner_id: int, name: str, rarity: CardRarity = CardRarity.rare, is_fake: bool = False) -> Card:
    return Card(
        owner_id=owner_id,
        name=name,
        description="desc",
        image_url="http://example.com/image.jpg",
        rarity=rarity,
        price=100,
        power=10,
        defense=5,
        is_fake=is_fake,
    )


def test_execute_trade_swaps_card_owners_and_creates_trade(db_session, monkeypatch):
    notifications = []
    monkeypatch.setattr(
        "app.services.trade_service.send_trade_email_notifications.delay",
        lambda requester_email, responder_email, trade_id: notifications.append(
            (requester_email, responder_email, trade_id)
        ),
    )

    requester = create_user("user_a", "a@example.com")
    responder = create_user("user_b", "b@example.com")
    db_session.add_all([requester, responder])
    db_session.commit()
    db_session.refresh(requester)
    db_session.refresh(responder)

    offered_card = create_card(requester.id, "Dragon")
    requested_card = create_card(responder.id, "Phoenix")
    db_session.add_all([offered_card, requested_card])
    db_session.commit()
    db_session.refresh(offered_card)
    db_session.refresh(requested_card)

    trade = TradeService(db_session).execute_trade(requester, offered_card.id, requested_card.id)

    assert trade.status == TradeStatus.completed
    assert offered_card.owner_id == responder.id
    assert requested_card.owner_id == requester.id
    assert notifications == [("a@example.com", "b@example.com", trade.id)]


def test_execute_trade_rejects_when_requester_does_not_own_offered_card(db_session):
    requester = create_user("user_a", "a@example.com")
    responder = create_user("user_b", "b@example.com")
    db_session.add_all([requester, responder])
    db_session.commit()
    db_session.refresh(requester)
    db_session.refresh(responder)

    offered_card = create_card(responder.id, "Dragon")
    requested_card = create_card(responder.id, "Phoenix")
    db_session.add_all([offered_card, requested_card])
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        TradeService(db_session).execute_trade(requester, offered_card.id, requested_card.id)

    assert exc_info.value.status_code == 403


def test_execute_trade_rejects_fake_cards(db_session):
    requester = create_user("user_a", "a@example.com")
    responder = create_user("user_b", "b@example.com")
    db_session.add_all([requester, responder])
    db_session.commit()
    db_session.refresh(requester)
    db_session.refresh(responder)

    offered_card = create_card(requester.id, "Dragon", is_fake=True)
    requested_card = create_card(responder.id, "Phoenix")
    db_session.add_all([offered_card, requested_card])
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        TradeService(db_session).execute_trade(requester, offered_card.id, requested_card.id)

    assert exc_info.value.status_code == 400


def test_execute_trade_rejects_same_card(db_session):
    requester = create_user("user_a", "a@example.com")
    db_session.add(requester)
    db_session.commit()
    db_session.refresh(requester)

    card = create_card(requester.id, "Dragon")
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)

    with pytest.raises(HTTPException) as exc_info:
        TradeService(db_session).execute_trade(requester, card.id, card.id)

    assert exc_info.value.status_code == 400
