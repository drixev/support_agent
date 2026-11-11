from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

TICKET_ID_PATTERN = r"^TCK-\d{4}$"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    
class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True) # inmutable
    
    id: str = Field(pattern=TICKET_ID_PATTERN)
    title: str = Field(min_length=3, max_length=200)
    description: str
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
ALLOWED_TRANSITIONS:  dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.OPEN: frozenset({TicketStatus.IN_PROGRESS, TicketStatus.CLOSED}),
    TicketStatus.IN_PROGRESS: frozenset({TicketStatus.RESOLVED,TicketStatus.OPEN }),
    TicketStatus.RESOLVED: frozenset({TicketStatus.CLOSED, TicketStatus.IN_PROGRESS}),
    TicketStatus.CLOSED: frozenset()
}

