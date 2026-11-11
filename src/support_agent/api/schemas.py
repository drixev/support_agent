from datetime import datetime

from pydantic import BaseModel

from support_agent.domain.models import TicketStatus


class TicketOut(BaseModel):
    id: str
    title: str
    status: TicketStatus
    created_at: datetime