from typing import Annotated

from fastapi import APIRouter, Path, Query

from support_agent.api.dependencies import TicketServiceDep
from support_agent.api.schemas import TicketOut
from support_agent.domain.models import TICKET_ID_PATTERN

router = APIRouter(prefix="/tickets",tags=["tickets"])

@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: Annotated[str, Path(pattern=TICKET_ID_PATTERN)],
    service: TicketServiceDep
) -> TicketOut:
    ticket = await service.get_ticket(ticket_id)
    return TicketOut.model_validate(ticket, from_attributes=True)

@router.get("", response_model=list[TicketOut])
async def search_tickets(q: Annotated[str, Query(min_length=2)],
                         service: TicketServiceDep,
                         limit: Annotated[int, Query(ge=1, le=50)] = 10,
                        ):
    tickets = await service.search_tickets(q, limit)
    return [TicketOut.model_validate(t, from_attributes=True) for t in tickets]