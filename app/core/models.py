from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class EventRequest(BaseModel):
    event_id: str
    ticket_id: str
    event_type: str
    payload: Dict[str, Any]
    retry_count: int = 0


class Event(BaseModel):
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: Optional[datetime] = None


class Ticket(BaseModel):
    ticket_id: str
    current_state: str
    last_event_id: str

