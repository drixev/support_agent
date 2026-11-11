from typing import Protocol

from support_agent.domain.models import Ticket


class TicketRepository(Protocol):
    async def get(self, ticket_id:str) -> Ticket | None: ...
    async def search(self, query: str, limit: int = 10) -> list[Ticket]: ...