from app.db_models import DeadLetterEventDB

MAX_RETRIES = 3

def move_to_dlq(event, error_reason, db):
    dlq_event = DeadLetterEventDB(
        event_id=event.event_id,
        ticket_id=event.ticket_id,
        event_type=event.event_type,
        payload=event.payload,
        error_reason=error_reason,
        retry_count=event.retry_count,
    )
    db.add(dlq_event)
    db.commit()

