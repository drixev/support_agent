import pytest
from httpx import ASGITransport, AsyncClient

from support_agent.api.dependencies import get_ticket_service
from support_agent.application.ticket_service import TicketService
from support_agent.infraestructure.repositories.in_memory import InMemoryTicketRepository
from support_agent.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    repo = InMemoryTicketRepository.seeded()
    app.dependency_overrides[get_ticket_service] = lambda: TicketService(repo)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
        
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.json() == {"status": "ok"}
    

async def test_get_ticket_ok(client: AsyncClient):
    r = await client.get("/tickets/TCK-0001")
    assert r.status_code == 200
    assert r.json()["status"] == "open"
    
@pytest.mark.parametrize(("ticket_id", "expected"), [("TCK-9999", 404),("abc", 422)])
async def test_get_ticket_errors(client:AsyncClient, ticket_id:str, expected: int):
    r = await client.get(f"/tickets/{ticket_id}")
    assert r.status_code == expected


async def test_search_tickets_case_insensitive(client:AsyncClient):
    r = await client.get("/tickets", params = {"q":"SSO"})
    assert r.status_code == 200
    body = r.json()
    assert [t["id"] for t in body] == ["TCK-0001"]

async def test_search_tickets_matches_description(client:AsyncClient):
    r = await client.get("/tickets", params={"q":"timeout"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == ["TCK-0002"]
    
async def test_search_tickets_respects_limit(client: AsyncClient):
    # "e" aparece en ambos tickets, pero q necesita min 2 chars -> usamos "er"/"lo"
    r = await client.get("/tickets", params={"q":"lo", "limit": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1
    
    
@pytest.mark.parametrize(
      "params",
      [
          {"q": "sso", "limit": 0},
          {"q": "sso", "limit": 51},
          {"q": "s"},   # q demasiado corto
          {},           # q ausente
      ],
  )
async def test_search_tickets_invalid_params(client: AsyncClient, params: dict):
      r = await client.get("/tickets", params=params)
      assert r.status_code == 422