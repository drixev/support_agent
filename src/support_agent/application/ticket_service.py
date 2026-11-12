from support_agent.domain.errors import InvalidStatusTransitionError, TicketNotFoundError
from support_agent.domain.models import ALLOWED_TRANSITIONS, Ticket, TicketStatus
from support_agent.domain.ports import TicketRepository


class TicketService:
    def __init__(self, repo:TicketRepository)-> None:
        self._repo = repo
        
    async def get_ticket(self, ticket_id:str)-> Ticket:
        ticket = await self._repo.get(ticket_id)
        
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        
        return ticket
    
    async def search_tickets(self, query:str, limit:int = 10) -> list[Ticket]:
        return await self._repo.search(query.strip(), limit)
    
    async def update_status(self, ticket_id:str, new_status:TicketStatus) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        if new_status not in ALLOWED_TRANSITIONS[ticket.status]:
            raise InvalidStatusTransitionError(ticket.status, new_status)

        updated = ticket.model_copy(update={"status": new_status})
        await self._repo.save(updated)
        return updated