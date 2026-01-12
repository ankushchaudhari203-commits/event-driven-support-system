from app.core.errors import RetryableError, NonRetryableError

def process_event(event, ticket, db):
    if not event.payload:
        raise NonRetryableError("Empty payload")

    if event.event_type == "EXTERNAL_CALL":
        if external_service_timed_out():
            raise RetryableError("External service timeout")

    # existing logic continues

