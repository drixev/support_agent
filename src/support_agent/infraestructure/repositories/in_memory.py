from itertools import islice

from support_agent.domain.models import Ticket, TicketStatus


class InMemoryTicketRepository: # cumple TicketRepository sin heredar
    def __init__(self, tickets: list[Ticket] | None = None) -> None:
        self._tickets: dict[str, Ticket] = {t.id: t for t in tickets or []}
    
    @classmethod
    def seeded(cls) -> "InMemoryTicketRepository":
        return cls([
            Ticket(
                id="TCK-0001", 
                title="Login falla con SSO", 
                description="Error 500 al volver del IdP"),
            Ticket(
                id="TCK-0002", 
                title="Explorar CSV lento", 
                description="Timeout con más de 10k filas", 
                status=TicketStatus.IN_PROGRESS),
        ])
        
    async def get(self, ticket_id:str)-> Ticket | None:
        return self._tickets.get(ticket_id)
    
    async def search(self, query:str, limit:int = 10)-> list[Ticket]:
        needle = query.casefold()
        matches = (
            t for t in self._tickets.values()
            if needle in t.title.casefold() or needle in t.description.casefold()
        )
        
        return list(islice(matches, limit))

    async def save(self, ticket:Ticket) -> None:
        self._tickets[ticket.id] = ticket