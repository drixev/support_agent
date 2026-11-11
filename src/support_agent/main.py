from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from support_agent.api.routes import health, tickets
from support_agent.config import get_settings
from support_agent.domain.errros import TicketNotFoundError
from support_agent.infraestructure.repositories.in_memory import InMemoryTicketRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.ticket_repo = InMemoryTicketRepository.seeded() # startup
    yield
    # shutdown: cerrar pools/clientes aqui
    
def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="Support Agent", 
        version="0.1.0", 
        lifespan=lifespan, 
        debug=settings.env == "local"
        )
    app.include_router(health.router)    
    app.include_router(tickets.router)    
    
    @app.exception_handler(TicketNotFoundError)
    async def _not_found(_:Request, exc:TicketNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    
    return app

app = create_app()