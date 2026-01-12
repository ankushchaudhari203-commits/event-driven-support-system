from fastapi import FastAPI
from datetime import datetime
from uuid import uuid4

from app.core.models import EventRequest
from app.db import engine, SessionLocal, Base
from app.db_models import EventDB, TicketDB, ProcessedEventDB
from app.core.errors import RetryableError, NonRetryableError
from app.core.dlq import move_to_dlq, MAX_RETRIES


app = FastAPI()
Base.metadata.create_all(bind=engine)


TICKET_STATES = {
    "OPEN": "OPEN",
    "PROCESSING": "PROCESSING",
    "RESOLVED": "RESOLVED"
}


@app.get("/")
def health_check():
    return {"status": "Event-driven support system is running"}


def transition_state(current_state: str | None, event_type: str):
    if current_state is None and event_type == "MESSAGE_RECEIVED":
        return TICKET_STATES["OPEN"]

    if current_state == TICKET_STATES["OPEN"] and event_type == "MESSAGE_RECEIVED":
        return TICKET_STATES["PROCESSING"]

    if current_state == TICKET_STATES["PROCESSING"] and event_type == "RESOLVE":
        return TICKET_STATES["RESOLVED"]

    return None


@app.post("/events")
def create_event(request: EventRequest):
    db = SessionLocal()

    try:
        # ----------------------------
        # Global idempotency
        # ----------------------------
        if db.get(ProcessedEventDB, request.event_id):
            return {
                "status": "IGNORED",
                "reason": "Duplicate event",
                "event_id": request.event_id
            }

        # ----------------------------
        # Lock latest ticket
        # ----------------------------
        ticket = (
            db.query(TicketDB)
            .order_by(TicketDB.created_at.desc())
            .with_for_update()
            .first()
        )

        # ----------------------------
        # Per-ticket idempotency
        # ----------------------------
        if ticket:
            for h in ticket.state_history:
                if h["event_id"] == request.event_id:
                    return {
                        "status": "IGNORED",
                        "reason": "Duplicate event for this ticket",
                        "event_id": request.event_id,
                        "ticket_id": ticket.ticket_id
                    }

        # ----------------------------
        # State transition
        # ----------------------------
        current_state = ticket.current_state if ticket else None
        next_state = transition_state(current_state, request.event_type)

        if next_state is None:
            raise NonRetryableError("Invalid state transition")

        # ----------------------------
        # Create or update ticket
        # ----------------------------
        if ticket is None:
            ticket = TicketDB(
                ticket_id=str(uuid4()),
                current_state=next_state,
                last_event_id=request.event_id,
                created_at=datetime.utcnow(),
                state_history=[{
                    "from": None,
                    "to": next_state,
                    "event_id": request.event_id,
                    "timestamp": datetime.utcnow().isoformat()
                }]
            )
            db.add(ticket)

        else:
            history = ticket.state_history
            history.append({
                "from": current_state,
                "to": next_state,
                "event_id": request.event_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            ticket.state_history = history
            ticket.current_state = next_state
            ticket.last_event_id = request.event_id

        # ----------------------------
        # Record event + idempotency
        # ----------------------------
        db.add(EventDB(
            event_id=request.event_id,
            event_type=request.event_type,
            payload=request.payload,
            status="RECEIVED",
            created_at=datetime.utcnow()
        ))

        db.add(ProcessedEventDB(event_id=request.event_id))

        db.commit()

        return {
            "status": "PROCESSED",
            "ticket_id": ticket.ticket_id,
            "current_state": ticket.current_state
        }

    # ----------------------------
    # RETRYABLE FAILURE
    # ----------------------------
    except RetryableError as e:
        db.rollback()

        if request.retry_count < MAX_RETRIES:
            request.retry_count += 1
            raise  # simulate retry (queue behavior)

        move_to_dlq(request, str(e), db)
        return {
            "status": "DLQ",
            "reason": str(e)
        }

    # ----------------------------
    # NON-RETRYABLE FAILURE
    # ----------------------------
    except NonRetryableError as e:
        db.rollback()
        move_to_dlq(request, str(e), db)
        return {
            "status": "DLQ",
            "reason": str(e)
        }

    finally:
        db.close()

