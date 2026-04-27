from app.celery_app import celery_app


@celery_app.task(name="trade.send_trade_email_notifications")
def send_trade_email_notifications(requester_email: str, responder_email: str, trade_id: int) -> None:
    # Replace with a real email backend in production.
    print(
        f"Trade {trade_id} completed. Notifications queued for "
        f"{requester_email} and {responder_email}."
    )
