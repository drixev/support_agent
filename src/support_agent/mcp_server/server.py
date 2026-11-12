import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from support_agent.application.ticket_service import TicketService
from support_agent.domain.models import TICKET_ID_PATTERN, Ticket, TicketStatus
from support_agent.infrastructure.repositories.in_memory import InMemoryTicketRepository

# stdio: stdio es el canal JSON-RPC -> logs SOLO a stderr

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("support_agent.mcp")



@dataclass(frozen=True)
class AppContext:
    service: TicketService
    
    
@asynccontextmanager
async def lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
    # ~~ lifespan de FastAPI. En fases sigueintes: pool de postgress aquí
    yield AppContext(service=TicketService(InMemoryTicketRepository.seeded()))
    

mcp = FastMCP("support-tickets", lifespan=lifespan)

TicketId = Annotated[
    str,
    Field(pattern=TICKET_ID_PATTERN, description="Ticket ID, format TCK-0000")
]

class TicketView(BaseModel):
    """DTO de salida de la tool: el contrato MCP no expone la entidad tal cual"""
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    status: TicketStatus    

class SearchResult(BaseModel):
    tickets: list[TicketView]
    count: int

def _service(ctx: Context) -> TicketService:
    return ctx.request_context.lifespan_context.service

def _view(t: Ticket) -> TicketView:
    return TicketView.model_validate(t)



READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)


@mcp.tool(annotations=READ_ONLY)
async def search_tickets(
    query: Annotated[str, Field(min_length=2, max_length=200, 
                                description="Keywords to match in title/description")],
    ctx: Context,
    limit: Annotated[int, Field(ge=1, le=20)] = 5
) -> SearchResult:
    """Search support tickets by keyword. Read-only. Use before get_tickets if the ID is unknown."""
    tickets = await _service(ctx).search_tickets(query, limit)
    return SearchResult(tickets=[_view(t) for t in tickets], count=len(tickets))


@mcp.tool(annotations=READ_ONLY)
async def get_ticket(ticket_id:TicketId, ctx: Context) -> TicketView:
    """Get the full details of a single ticket by its ID. read-only"""
    return _view(await _service(ctx).get_ticket(ticket_id))


@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False
))
async def update_ticket_status(
    ticket_id:TicketId,
    new_status:TicketStatus,
    reason: Annotated[str, Field(min_length=5, max_length=500, 
                                 description="Why the status change (audit log)")],
    
    ctx:Context,
) -> TicketView:
    """Change a ticket's status. WRITE operation: requires human approval in the agent.
    Valid transitions: open -> in_progress|close, in_progress -> resovled|open, 
    resolved -> closed|in_progress."""
    updated = await _service(ctx).update_status(ticket_id, new_status)
    log.info("AUDIT update_ticket_status id=%s status=%s reason=%r", ticket_id, new_status, reason)
    
    return _view(updated)

if __name__ == "__main__":
    mcp.run()