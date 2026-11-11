from support_agent.domain.errros import TicketNotFoundError
from support_agent.domain.models import Ticket
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