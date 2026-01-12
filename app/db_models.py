from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime
from app.db import Base
from sqlalchemy import Integer, UniqueConstraint

class EventDB(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String)
    payload = Column(JSON)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class TicketDB(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True, index=True)
    current_state = Column(String)
    last_event_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    state_history = Column(JSON)


class ProcessedEventDB(Base):
    __tablename__ = "processed_events"

    event_id = Column(String, primary_key=True, index=True)
    
class DeadLetterEventDB(Base):
    __tablename__ = "dead_letter_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, nullable=False)
    ticket_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)

    error_reason = Column(String, nullable=False)
    retry_count = Column(Integer, default=0)
    status = Column(String, default="PENDING")
    failed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("event_id", "ticket_id"),
    )

