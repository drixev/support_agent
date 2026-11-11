from typing import Annotated

from fastapi import Depends, Request

from support_agent.application.ticket_service import TicketService


def get_ticket_service(request: Request) -> TicketService:
    return TicketService(request.app.state.ticket_repo)

TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]